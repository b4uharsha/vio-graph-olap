{{/*
ServiceAccount templates for Graph OLAP Platform Helm charts.
*/}}

{{/*
ServiceAccount definition with Workload Identity support.
Usage: {{ include "common.serviceaccount" . }}
*/}}
{{- define "common.serviceaccount" -}}
{{- if .Values.serviceAccount.create -}}
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ include "common.names.serviceAccountName" . }}
  namespace: {{ include "common.names.namespace" . }}
  labels:
    {{- include "common.labels.standard" . | nindent 4 }}
  {{- if or .Values.serviceAccount.annotations (and .Values.serviceAccount.gcpServiceAccount .Values.global.gcpProject) }}
  annotations:
    {{- if and .Values.serviceAccount.gcpServiceAccount .Values.global.gcpProject }}
    iam.gke.io/gcp-service-account: {{ .Values.serviceAccount.gcpServiceAccount }}@{{ .Values.global.gcpProject }}.iam.gserviceaccount.com
    {{- end }}
    {{- with .Values.serviceAccount.annotations }}
    {{- toYaml . | nindent 4 }}
    {{- end }}
  {{- end }}
{{- if .Values.serviceAccount.automountServiceAccountToken }}
automountServiceAccountToken: {{ .Values.serviceAccount.automountServiceAccountToken }}
{{- end }}
{{- if .Values.serviceAccount.imagePullSecrets }}
imagePullSecrets:
  {{- range .Values.serviceAccount.imagePullSecrets }}
  - name: {{ . }}
  {{- end }}
{{- end }}
{{- end }}
{{- end }}

{{/*
ServiceAccount reference for pod spec.
Usage: serviceAccountName: {{ include "common.serviceaccount.name" . }}
*/}}
{{- define "common.serviceaccount.name" -}}
{{ include "common.names.serviceAccountName" . }}
{{- end }}

{{/*
RBAC Role definition.
Usage: {{ include "common.rbac.role" (dict "context" . "rules" .Values.rbac.rules) }}
*/}}
{{- define "common.rbac.role" -}}
{{- if .context.Values.rbac.create -}}
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: {{ include "common.names.fullname" .context }}
  namespace: {{ include "common.names.namespace" .context }}
  labels:
    {{- include "common.labels.standard" .context | nindent 4 }}
rules:
  {{- toYaml .rules | nindent 2 }}
{{- end }}
{{- end }}

{{/*
RBAC RoleBinding definition.
Usage: {{ include "common.rbac.rolebinding" . }}
*/}}
{{- define "common.rbac.rolebinding" -}}
{{- if .Values.rbac.create -}}
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: {{ include "common.names.fullname" . }}
  namespace: {{ include "common.names.namespace" . }}
  labels:
    {{- include "common.labels.standard" . | nindent 4 }}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: {{ include "common.names.fullname" . }}
subjects:
  - kind: ServiceAccount
    name: {{ include "common.names.serviceAccountName" . }}
    namespace: {{ include "common.names.namespace" . }}
{{- end }}
{{- end }}
