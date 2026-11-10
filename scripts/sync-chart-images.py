#!/usr/bin/env python3
"""Sync Helm chart image tags with the newest Docker Hub semver tags.

Reads public tags for each AlertHawk image, and when a newer MAJOR.MINOR.PATCH
tag exists:

- replaces that tag in the chart values
- bumps the full `alerthawk` chart patch version
- sets `alerthawk.agent` and `alerthawk-metrics-agent` to the image tag they ship
- packages only the charts that changed and refreshes index.yaml
- keeps the two newest packages of each chart and deletes the rest
- writes chart-releases.jsonl so the GitHub Action can publish one release per chart

Tags named `latest`, `sha-*`, or anything that is not MAJOR.MINOR.PATCH are ignored.
An older Docker Hub tag never replaces a newer tag already in the chart.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAMESPACE = "thiagoguaru"
REPO_URL = "https://thiagoloureiro.github.io/AlertHawk.Chart/"
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
KEEP_VERSIONS = 2
RELEASE_MANIFEST = "chart-releases.jsonl"
CHART_FILES = (
    "alerthawk/Chart.yaml",
    "alerthawk.agent/Chart.yaml",
    "alerthawk.metrics.agent/Chart.yaml",
)

# repository -> values files that pin "namespace/repository:tag"
STACK_IMAGES = {
    "alerthawk.monitoring": ["alerthawk/values.yaml", "alerthawk.agent/values.yaml"],
    "alerthawk.authentication": ["alerthawk/values.yaml"],
    "alerthawk.notification": ["alerthawk/values.yaml"],
    "alerthawk.metrics.api": ["alerthawk/values.yaml"],
    "alerthawk.finops.api": ["alerthawk/values.yaml"],
    "alerthawk.ui-demo-v2": ["alerthawk/values.yaml"],
}
METRICS_IMAGE = "alerthawk.metrics"
METRICS_VALUES = "alerthawk.metrics.agent/values.yaml"


def parse_version(version: str) -> tuple[int, int, int]:
    major, minor, patch = version.split(".")
    return int(major), int(minor), int(patch)


def bump_patch(version: str) -> str:
    major, minor, patch = parse_version(version)
    return f"{major}.{minor}.{patch + 1}"


def set_output(key: str, value: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        if "\n" in value or "\r" in value:
            delimiter = "EOF_CHART_SYNC"
            handle.write(f"{key}<<{delimiter}\n{value}\n{delimiter}\n")
        else:
            handle.write(f"{key}={value}\n")


def write_summary(lines: list[str]) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path or not lines:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write("## Chart image sync\n\n")
        for line in lines:
            handle.write(f"- {line}\n")
        handle.write("\n")


def fetch_json(url: str) -> dict:
    delay = 1.0
    last_error: Exception | None = None
    for _ in range(5):
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "AlertHawk-Chart-sync",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in (429, 500, 502, 503, 504):
                raise
        except urllib.error.URLError as exc:
            last_error = exc
        time.sleep(delay)
        delay *= 2
    raise SystemExit(f"Docker Hub request failed for {url}: {last_error}")


def latest_semver(repository: str) -> str:
    url = (
        f"https://hub.docker.com/v2/repositories/{NAMESPACE}/{repository}/tags"
        "?page_size=100&ordering=last_updated"
    )
    best: tuple[tuple[int, int, int], str] | None = None
    pages = 0
    while url:
        pages += 1
        if pages > 30:
            break
        payload = fetch_json(url)
        for item in payload.get("results") or []:
            name = item.get("name") or ""
            status = item.get("tag_status") or "active"
            if status != "active" or not SEMVER_RE.match(name):
                continue
            parsed = parse_version(name)
            if best is None or parsed > best[0]:
                best = (parsed, name)
        url = payload.get("next")
    if best is None:
        raise SystemExit(f"No semver tag found for {NAMESPACE}/{repository}")
    return best[1]


def chart_field(text: str, field: str) -> str:
    match = re.search(rf"^{field}:\s*(\S+)", text, re.MULTILINE)
    if not match:
        raise SystemExit(f"{field} not found in Chart.yaml")
    return match.group(1)


def replace_chart_version(text: str, version: str) -> str:
    updated, version_count = re.subn(
        r"^(version:\s*)\S+",
        rf"\g<1>{version}",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    updated, app_count = re.subn(
        r'^(appVersion:\s*")[^"]+(")',
        rf"\g<1>{version}\2",
        updated,
        count=1,
        flags=re.MULTILINE,
    )
    if version_count != 1 or app_count != 1:
        raise SystemExit("failed to update chart version and appVersion")
    return updated


def current_image_tag(text: str, repository: str) -> str:
    match = re.search(
        rf"{re.escape(NAMESPACE)}/{re.escape(repository)}:(\d+\.\d+\.\d+)",
        text,
    )
    if not match:
        raise SystemExit(f"current tag for {NAMESPACE}/{repository} not found")
    return match.group(1)


def replace_image_tag(text: str, repository: str, new_tag: str) -> str:
    updated, count = re.subn(
        rf"({re.escape(NAMESPACE)}/{re.escape(repository)}:)(\d+\.\d+\.\d+)",
        rf"\g<1>{new_tag}",
        text,
    )
    if count < 1:
        raise SystemExit(f"{NAMESPACE}/{repository} not found while replacing tag")
    return updated


def current_metrics_tag(text: str) -> str:
    match = re.search(r'^\s*tag:\s*"(\d+\.\d+\.\d+)"', text, re.MULTILINE)
    if not match:
        raise SystemExit(f"image tag not found in {METRICS_VALUES}")
    return match.group(1)


def replace_metrics_tag(text: str, new_tag: str) -> str:
    updated, count = re.subn(
        r'^(\s*tag:\s*")(\d+\.\d+\.\d+)(")',
        rf"\g<1>{new_tag}\3",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise SystemExit(f"failed to update image tag in {METRICS_VALUES}")
    return updated


def next_free_version(chart_name: str, desired: str) -> str:
    version = desired
    seen: set[str] = set()
    while (ROOT / f"{chart_name}-{version}.tgz").exists():
        if version in seen:
            raise SystemExit(f"could not find a free version for {chart_name}")
        seen.add(version)
        version = bump_patch(version)
    return version


def plan_version(chart_text: str, mode: str, image_tag: str | None) -> tuple[str, str, str]:
    name = chart_field(chart_text, "name")
    current = chart_field(chart_text, "version")
    if mode == "patch":
        desired = bump_patch(current)
    elif image_tag and parse_version(image_tag) > parse_version(current):
        desired = image_tag
    else:
        desired = bump_patch(current)
    return name, current, next_free_version(name, desired)


def ensure_alerthawk_dependencies() -> None:
    """Use the ClickHouse chart already vendored in alerthawk/charts/.

    `helm package` refuses to build the parent chart when that archive is missing.
    Download it only in that case, and leave the directory in place: it is part of
    the repository, not a temporary build product.
    """
    charts_dir = ROOT / "alerthawk" / "charts"
    if any(charts_dir.glob("*.tgz")):
        return
    subprocess.check_call(
        [
            "helm",
            "repo",
            "add",
            "clickhouse",
            "https://thiagoloureiro.github.io/clickhouse.chart/",
        ],
        cwd=ROOT,
    )
    subprocess.check_call(["helm", "dependency", "build", "alerthawk"], cwd=ROOT)


def require_helm() -> None:
    if shutil.which("helm") is None:
        raise SystemExit("helm is required to package charts")


def package_names() -> list[str]:
    names = [chart_field((ROOT / rel).read_text(), "name") for rel in CHART_FILES]
    return sorted(names, key=len, reverse=True)


def split_archive(filename: str, names: list[str]) -> tuple[str, str] | None:
    if not filename.endswith(".tgz"):
        return None
    stem = filename[: -len(".tgz")]
    for name in names:
        prefix = f"{name}-"
        if not stem.startswith(prefix):
            continue
        version = stem[len(prefix) :]
        if SEMVER_RE.match(version):
            return name, version
    return None


def prune_old_packages(keep: int = KEEP_VERSIONS) -> list[str]:
    """Delete packaged charts beyond the newest `keep` versions of each chart."""
    grouped: dict[str, list[tuple[tuple[int, int, int], Path]]] = {}
    for path in ROOT.glob("*.tgz"):
        parsed = split_archive(path.name, package_names())
        if parsed is None:
            continue
        name, version = parsed
        grouped.setdefault(name, []).append((parse_version(version), path))

    removed: list[str] = []
    for items in grouped.values():
        items.sort(reverse=True)
        for _version, path in items[keep:]:
            path.unlink()
            removed.append(path.name)
            print(f"removed {path.name}")
    return removed


def release_tag(chart_name: str, version: str) -> str:
    # The full chart uses a semver tag so the repository's latest-release badge tracks it.
    if chart_name == "alerthawk":
        return f"v{version}"
    return f"{chart_name}-{version}"


def release_notes(chart_name: str, version: str, changes: list[tuple[str, str, str]]) -> str:
    if chart_name == "alerthawk.agent":
        relevant = [change for change in changes if change[0] == "alerthawk.monitoring"]
    elif chart_name == "alerthawk-metrics-agent":
        relevant = [change for change in changes if change[0] == METRICS_IMAGE]
    else:
        relevant = [change for change in changes if change[0] in STACK_IMAGES]
    lines = [f"Helm chart `{chart_name}` `{version}`.", "", "Images:"]
    for repository, old, new in relevant:
        lines.append(f"- `{NAMESPACE}/{repository}` {old} -> {new}")
    lines.extend(["", f"Install from `{REPO_URL}`."])
    return "\n".join(lines)


def write_release_manifest(
    plans: list[tuple[str, str, str, str, str]],
    changes: list[tuple[str, str, str]],
) -> None:
    records = []
    for _chart_file, _chart_dir, name, _current, version in plans:
        asset = f"{name}-{version}.tgz"
        if not (ROOT / asset).is_file():
            raise SystemExit(f"missing package for release: {asset}")
        records.append(
            {
                "tag": release_tag(name, version),
                "title": f"{name} {version}",
                "asset": asset,
                "latest": name == "alerthawk",
                "notes": release_notes(name, version, changes),
            }
        )
    (ROOT / RELEASE_MANIFEST).write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )
    for record in records:
        print(f"release {record['tag']} ({record['asset']})")


def reindex() -> None:
    require_helm()
    subprocess.check_call(
        ["helm", "repo", "index", str(ROOT), "--url", REPO_URL],
        cwd=ROOT,
    )


def package_charts(updates: list[tuple[str, str, str]]) -> None:
    """Package changed charts into the repository root.

    `updates` entries are (chart directory, package name, version).
    The caller refreshes index.yaml after pruning older packages.
    """
    require_helm()

    if any(chart_dir == "alerthawk" for chart_dir, _name, _version in updates):
        ensure_alerthawk_dependencies()

    output = Path(tempfile.mkdtemp(prefix="alerthawk-charts-"))
    try:
        for chart_dir, name, version in updates:
            subprocess.check_call(
                ["helm", "package", chart_dir, "--destination", str(output)],
                cwd=ROOT,
            )
            expected = output / f"{name}-{version}.tgz"
            if not expected.is_file():
                found = ", ".join(path.name for path in output.glob("*.tgz")) or "(none)"
                raise SystemExit(f"expected {expected.name}, helm wrote: {found}")

        for archive in output.glob("*.tgz"):
            destination = ROOT / archive.name
            if destination.exists():
                raise SystemExit(f"refusing to overwrite {destination.name}")
            shutil.move(str(archive), destination)
    finally:
        shutil.rmtree(output, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the image and chart version changes without writing files",
    )
    args = parser.parse_args()
    manifest = ROOT / RELEASE_MANIFEST
    if manifest.exists():
        manifest.unlink()

    repositories = list(STACK_IMAGES) + [METRICS_IMAGE]
    latest = {repository: latest_semver(repository) for repository in repositories}

    paths = {METRICS_VALUES}
    for files in STACK_IMAGES.values():
        paths.update(files)
    originals = {rel: (ROOT / rel).read_text() for rel in sorted(paths)}
    updated = dict(originals)

    image_notes: list[str] = []
    image_changes: list[tuple[str, str, str]] = []
    new_tags: dict[str, str] = {}

    for repository, files in STACK_IMAGES.items():
        current = current_image_tag(originals[files[0]], repository)
        new = latest[repository]
        if parse_version(new) < parse_version(current):
            print(f"{repository}: Docker Hub {new} is behind chart {current}; keeping {current}")
            continue
        if new == current:
            print(f"{repository}: {current} (unchanged)")
            continue
        print(f"{repository}: {current} -> {new}")
        image_notes.append(f"`{NAMESPACE}/{repository}` {current} -> {new}")
        image_changes.append((repository, current, new))
        new_tags[repository] = new
        for rel in files:
            updated[rel] = replace_image_tag(updated[rel], repository, new)

    metrics_current = current_metrics_tag(originals[METRICS_VALUES])
    metrics_new = latest[METRICS_IMAGE]
    if parse_version(metrics_new) < parse_version(metrics_current):
        print(
            f"{METRICS_IMAGE}: Docker Hub {metrics_new} is behind chart {metrics_current}; "
            f"keeping {metrics_current}"
        )
    elif metrics_new == metrics_current:
        print(f"{METRICS_IMAGE}: {metrics_current} (unchanged)")
    else:
        print(f"{METRICS_IMAGE}: {metrics_current} -> {metrics_new}")
        image_notes.append(f"`{NAMESPACE}/{METRICS_IMAGE}` {metrics_current} -> {metrics_new}")
        image_changes.append((METRICS_IMAGE, metrics_current, metrics_new))
        new_tags[METRICS_IMAGE] = metrics_new
        updated[METRICS_VALUES] = replace_metrics_tag(updated[METRICS_VALUES], metrics_new)

    if not new_tags:
        removed = [] if args.dry_run else prune_old_packages()
        if args.dry_run or not removed:
            print("No image updates.")
            set_output("changed", "false")
            return 0
        reindex()
        message = "Keep the two newest packages of each Helm chart."
        print(message)
        set_output("changed", "true")
        set_output("message", message)
        write_summary([f"removed `{name}`" for name in removed])
        print("Updated index.yaml.")
        return 0

    chart_plans: list[tuple[str, str, str, str, str]] = []
    # (chart yaml, chart dir, package name, old version, new version)
    if any(repository in new_tags for repository in STACK_IMAGES):
        chart_plans.append(("alerthawk/Chart.yaml", "alerthawk", *plan_tail("alerthawk/Chart.yaml", "patch", None)))
    if "alerthawk.monitoring" in new_tags:
        chart_plans.append(
            (
                "alerthawk.agent/Chart.yaml",
                "alerthawk.agent",
                *plan_tail(
                    "alerthawk.agent/Chart.yaml",
                    "image",
                    new_tags["alerthawk.monitoring"],
                ),
            )
        )
    if METRICS_IMAGE in new_tags:
        chart_plans.append(
            (
                "alerthawk.metrics.agent/Chart.yaml",
                "alerthawk.metrics.agent",
                *plan_tail(
                    "alerthawk.metrics.agent/Chart.yaml",
                    "image",
                    new_tags[METRICS_IMAGE],
                ),
            )
        )

    version_notes = []
    for chart_file, _chart_dir, name, current, version in chart_plans:
        print(f"{name}: chart {current} -> {version}")
        version_notes.append(f"`{name}` chart {current} -> {version}")

    names = ", ".join(f"{name} {version}" for _f, _d, name, _c, version in chart_plans)
    message = (
        f"Update {names}; sync image tags from Docker Hub and regenerate the Helm index."
    )
    print(message)

    if args.dry_run:
        for _chart_file, _chart_dir, name, _current, version in chart_plans:
            print(f"release {release_tag(name, version)} ({name}-{version}.tgz)")
        set_output("changed", "false")
        return 0

    for rel, text in updated.items():
        if text != originals[rel]:
            (ROOT / rel).write_text(text)
    for chart_file, _chart_dir, _name, _current, version in chart_plans:
        path = ROOT / chart_file
        path.write_text(replace_chart_version(path.read_text(), version))

    package_charts(
        [(chart_dir, name, version) for _f, chart_dir, name, _c, version in chart_plans]
    )
    removed = prune_old_packages()
    reindex()
    write_release_manifest(chart_plans, image_changes)
    set_output("changed", "true")
    set_output("message", message)
    write_summary(image_notes + version_notes + [f"removed `{name}`" for name in removed])
    print("Updated index.yaml.")
    return 0


def plan_tail(chart_file: str, mode: str, image_tag: str | None) -> tuple[str, str, str]:
    return plan_version((ROOT / chart_file).read_text(), mode, image_tag)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as exc:
        command = " ".join(exc.cmd) if isinstance(exc.cmd, list) else str(exc.cmd)
        raise SystemExit(f"command failed ({exc.returncode}): {command}")
