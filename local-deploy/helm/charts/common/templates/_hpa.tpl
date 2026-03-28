{{/*
HorizontalPodAutoscaler templates for Graph OLAP Platform Helm charts.
*/}}

{{/*
Standard HPA with CPU and memory metrics.
Usage: {{ include "common.hpa" . }}
*/}}
{{- define "common.hpa" -}}
{{- if .Values.autoscaling.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "common.names.fullname" . }}
  namespace: {{ include "common.names.namespace" . }}
  labels:
    {{- include "common.labels.standard" . | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: {{ .Values.autoscaling.targetKind | default "Deployment" }}
    name: {{ include "common.names.fullname" . }}
  minReplicas: {{ .Values.autoscaling.minReplicas | default 2 }}
  maxReplicas: {{ .Values.autoscaling.maxReplicas | default 10 }}
  metrics:
    {{- if .Values.autoscaling.targetCPUUtilizationPercentage }}
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ .Values.autoscaling.targetCPUUtilizationPercentage }}
    {{- end }}
    {{- if .Values.autoscaling.targetMemoryUtilizationPercentage }}
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: {{ .Values.autoscaling.targetMemoryUtilizationPercentage }}
    {{- end }}
    {{- with .Values.autoscaling.customMetrics }}
    {{- toYaml . | nindent 4 }}
    {{- end }}
  {{- if or .Values.autoscaling.behavior .Values.autoscaling.scaleDown .Values.autoscaling.scaleUp }}
  behavior:
    {{- if .Values.autoscaling.behavior }}
    {{- toYaml .Values.autoscaling.behavior | nindent 4 }}
    {{- else }}
    {{- if .Values.autoscaling.scaleDown }}
    scaleDown:
      {{- toYaml .Values.autoscaling.scaleDown | nindent 6 }}
    {{- end }}
    {{- if .Values.autoscaling.scaleUp }}
    scaleUp:
      {{- toYaml .Values.autoscaling.scaleUp | nindent 6 }}
    {{- end }}
    {{- end }}
  {{- end }}
{{- end }}
{{- end }}
