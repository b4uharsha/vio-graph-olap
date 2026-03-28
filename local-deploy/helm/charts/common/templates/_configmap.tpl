{{/*
ConfigMap templates for Graph OLAP Platform Helm charts.
*/}}

{{/*
Standard ConfigMap from data.
Usage: {{ include "common.configmap" (dict "context" . "data" .Values.config) }}
*/}}
{{- define "common.configmap" -}}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "common.names.fullname" .context }}
  namespace: {{ include "common.names.namespace" .context }}
  labels:
    {{- include "common.labels.standard" .context | nindent 4 }}
data:
  {{- range $key, $value := .data }}
  {{ $key }}: {{ $value | quote }}
  {{- end }}
{{- end }}

{{/*
ConfigMap with binary data.
Usage: {{ include "common.configmap.binary" (dict "context" . "binaryData" .Values.binaryConfig) }}
*/}}
{{- define "common.configmap.binary" -}}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "common.names.fullname" .context }}
  namespace: {{ include "common.names.namespace" .context }}
  labels:
    {{- include "common.labels.standard" .context | nindent 4 }}
binaryData:
  {{- range $key, $value := .binaryData }}
  {{ $key }}: {{ $value }}
  {{- end }}
{{- end }}

{{/*
Volume mount for ConfigMap.
Usage: {{ include "common.configmap.volumeMount" (dict "name" "config" "mountPath" "/etc/config") }}
*/}}
{{- define "common.configmap.volumeMount" -}}
- name: {{ .name }}
  mountPath: {{ .mountPath }}
  {{- if .subPath }}
  subPath: {{ .subPath }}
  {{- end }}
  readOnly: {{ .readOnly | default true }}
{{- end }}

{{/*
Volume definition for ConfigMap.
Usage: {{ include "common.configmap.volume" (dict "name" "config" "configMapName" "my-config") }}
*/}}
{{- define "common.configmap.volume" -}}
- name: {{ .name }}
  configMap:
    name: {{ .configMapName }}
    {{- if .items }}
    items:
      {{- toYaml .items | nindent 6 }}
    {{- end }}
    {{- if .defaultMode }}
    defaultMode: {{ .defaultMode }}
    {{- end }}
{{- end }}
