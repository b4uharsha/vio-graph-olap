{{/*
Jupyter Labs Helm Chart - Helper Templates
Uses graph-olap-common library for standard templates.
*/}}

{{/*
Expand the name of the chart.
*/}}
{{- define "jupyter-labs.name" -}}
{{- include "common.names.name" . }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "jupyter-labs.fullname" -}}
{{- include "common.names.fullname" . }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "jupyter-labs.chart" -}}
{{- include "common.names.chart" . }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "jupyter-labs.labels" -}}
{{ include "common.labels.standard" . }}
app: jupyter-labs
{{- end }}

{{/*
Selector labels
*/}}
{{- define "jupyter-labs.selectorLabels" -}}
{{ include "common.labels.matchLabels" . }}
app: jupyter-labs
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "jupyter-labs.serviceAccountName" -}}
{{- include "common.names.serviceAccountName" . }}
{{- end }}
