{{/*
Environment variable templates for Graph OLAP Platform Helm charts.
*/}}

{{/*
Render environment variables from a map.
Usage: {{ include "common.env.fromMap" .Values.env | nindent 12 }}
*/}}
{{- define "common.env.fromMap" -}}
{{- range $key, $value := . }}
- name: {{ $key }}
  value: {{ $value | quote }}
{{- end }}
{{- end }}

{{/*
Render environment variable from secret.
Usage: {{ include "common.env.fromSecret" (dict "name" "DATABASE_URL" "secretName" "my-secret" "secretKey" "db-url") | nindent 12 }}
*/}}
{{- define "common.env.fromSecret" -}}
- name: {{ .name }}
  valueFrom:
    secretKeyRef:
      name: {{ .secretName }}
      key: {{ .secretKey }}
{{- end }}

{{/*
Render environment variable from configmap.
Usage: {{ include "common.env.fromConfigMap" (dict "name" "LOG_LEVEL" "configMapName" "my-config" "configMapKey" "log-level") | nindent 12 }}
*/}}
{{- define "common.env.fromConfigMap" -}}
- name: {{ .name }}
  valueFrom:
    configMapKeyRef:
      name: {{ .configMapName }}
      key: {{ .configMapKey }}
{{- end }}

{{/*
Render environment variable from field ref (downward API).
Usage: {{ include "common.env.fromFieldRef" (dict "name" "POD_NAME" "fieldPath" "metadata.name") | nindent 12 }}
*/}}
{{- define "common.env.fromFieldRef" -}}
- name: {{ .name }}
  valueFrom:
    fieldRef:
      fieldPath: {{ .fieldPath }}
{{- end }}

{{/*
Standard Graph OLAP environment variables.
Usage: {{ include "common.env.standard" . | nindent 12 }}
*/}}
{{- define "common.env.standard" -}}
- name: POD_NAME
  valueFrom:
    fieldRef:
      fieldPath: metadata.name
- name: POD_NAMESPACE
  valueFrom:
    fieldRef:
      fieldPath: metadata.namespace
{{- if .Values.global.environment }}
- name: ENVIRONMENT
  value: {{ .Values.global.environment | quote }}
{{- end }}
{{- if .Values.global.gcpProject }}
- name: GCP_PROJECT
  value: {{ .Values.global.gcpProject | quote }}
{{- end }}
{{- end }}

{{/*
Logging environment variables.
Usage: {{ include "common.env.logging" .Values.logging | nindent 12 }}
*/}}
{{- define "common.env.logging" -}}
{{- if . }}
- name: LOG_LEVEL
  value: {{ .level | default "INFO" | quote }}
- name: LOG_FORMAT
  value: {{ .format | default "json" | quote }}
{{- end }}
{{- end }}
