{{/*
Common annotation templates for Graph OLAP Platform Helm charts.
*/}}

{{/*
Standard annotations for all resources.
Usage: {{ include "common.annotations.standard" . | nindent 4 }}
*/}}
{{- define "common.annotations.standard" -}}
{{- with .Values.global.commonAnnotations }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Pod annotations including Prometheus scraping configuration.
Usage: {{ include "common.annotations.pod" . | nindent 8 }}
*/}}
{{- define "common.annotations.pod" -}}
{{- if .Values.metrics.enabled }}
prometheus.io/scrape: "true"
prometheus.io/port: {{ .Values.metrics.port | default "9090" | quote }}
prometheus.io/path: {{ .Values.metrics.path | default "/metrics" | quote }}
{{- end }}
{{- with .Values.podAnnotations }}
{{ toYaml . }}
{{- end }}
{{- with .Values.global.commonAnnotations }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Checksum annotation for ConfigMap/Secret changes to trigger rollout.
Usage: {{ include "common.annotations.checksum" (dict "configmap" $configMapData) }}
*/}}
{{- define "common.annotations.checksum" -}}
{{- if .configmap }}
checksum/config: {{ .configmap | sha256sum }}
{{- end }}
{{- if .secret }}
checksum/secret: {{ .secret | sha256sum }}
{{- end }}
{{- end }}

{{/*
Workload Identity annotation for GKE.
Usage: {{ include "common.annotations.workloadIdentity" . }}
*/}}
{{- define "common.annotations.workloadIdentity" -}}
{{- if and .Values.serviceAccount.gcpServiceAccount .Values.global.gcpProject }}
iam.gke.io/gcp-service-account: {{ .Values.serviceAccount.gcpServiceAccount }}@{{ .Values.global.gcpProject }}.iam.gserviceaccount.com
{{- end }}
{{- end }}
