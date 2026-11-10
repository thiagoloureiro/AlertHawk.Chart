# Package the charts already in the tree and refresh index.yaml.
# To pull newer Docker Hub tags, bump chart versions, and package, run:
#   python3 scripts/sync-chart-images.py
helm package alerthawk
helm package alerthawk.metrics.agent
helm package alerthawk.agent
helm repo index --url  https://thiagoloureiro.github.io/AlertHawk.Chart/ .  
