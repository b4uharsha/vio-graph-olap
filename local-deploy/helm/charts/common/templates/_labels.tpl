{{/*
Common label templates for Graph OLAP Platform Helm charts.
These templates provide standardized Kubernetes labels following best practices.
*/}}

{{/*
Kubernetes standard labels.
Usage: {{ include "common.labels.standard" . | nindent 4 }}
*/}}
{{- define "common.labels.standard" -}}
app.kubernetes.io/name: {{ include "common.names.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/component: {{ .Values.component | default "application" }}
app.kubernetes.io/part-of: graph-olap
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ include "common.names.chart" . }}
{{- if .Values.global }}
{{- with .Values.global.commonLabels }}
{{ toYaml . }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Labels to use on deploy.spec.selector.matchLabels and target.template.metadata.labels.
These are immutable after creation, so we only include the minimum required.
Usage: {{ include "common.labels.matchLabels" . | nindent 6 }}
*/}}
{{- define "common.labels.matchLabels" -}}
app.kubernetes.io/name: {{ include "common.names.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Extended labels including app shorthand for monitoring/service mesh compatibility.
Usage: {{ include "common.labels.extended" . | nindent 4 }}
*/}}
{{- define "common.labels.extended" -}}
{{ include "common.labels.standard" . }}
app: {{ include "common.names.name" . }}
{{- if .Values.team }}
team: {{ .Values.team }}
{{- end }}
{{- if and .Values.global .Values.global.environment }}
environment: {{ .Values.global.environment }}
{{- end }}
{{- end }}

{{/*
Pod labels - includes match labels plus additional pod-specific labels.
Usage: {{ include "common.labels.pod" . | nindent 8 }}
*/}}
{{- define "common.labels.pod" -}}
{{ include "common.labels.matchLabels" . }}
app: {{ include "common.names.name" . }}
{{- if and .Values.global .Values.global.environment }}
environment: {{ .Values.global.environment }}
{{- end }}
{{- with .Values.podLabels }}
{{ toYaml . }}
{{- end }}
{{- end }}
