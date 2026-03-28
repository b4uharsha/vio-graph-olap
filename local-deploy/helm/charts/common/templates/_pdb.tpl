{{/*
PodDisruptionBudget templates for Graph OLAP Platform Helm charts.
*/}}

{{/*
Standard PDB.
Usage: {{ include "common.pdb" . }}
*/}}
{{- define "common.pdb" -}}
{{- if .Values.podDisruptionBudget.enabled }}
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: {{ include "common.names.fullname" . }}
  namespace: {{ include "common.names.namespace" . }}
  labels:
    {{- include "common.labels.standard" . | nindent 4 }}
spec:
  {{- if .Values.podDisruptionBudget.minAvailable }}
  minAvailable: {{ .Values.podDisruptionBudget.minAvailable }}
  {{- else if .Values.podDisruptionBudget.maxUnavailable }}
  maxUnavailable: {{ .Values.podDisruptionBudget.maxUnavailable }}
  {{- else }}
  minAvailable: 1
  {{- end }}
  selector:
    matchLabels:
      {{- include "common.labels.matchLabels" . | nindent 6 }}
  {{- if .Values.podDisruptionBudget.unhealthyPodEvictionPolicy }}
  unhealthyPodEvictionPolicy: {{ .Values.podDisruptionBudget.unhealthyPodEvictionPolicy }}
  {{- end }}
{{- end }}
{{- end }}
