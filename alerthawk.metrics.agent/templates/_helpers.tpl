{{- define "name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "fullname" -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "labels" -}}
app: {{ include "name" . }}
component: metrics
{{- with .Values.labels }}
{{- toYaml . }}
{{- end }}
{{- end -}}

{{- define "selectorLabels" -}}
app: {{ include "name" . }}
component: metrics
workload.user.cattle.io/workloadselector: apps.deployment-{{ .Release.Namespace }}-{{ include "name" . }}-metrics
{{- with .Values.selectorLabels }}
{{- toYaml . }}
{{- end }}
{{- end -}}