{{/*
Service templates for Graph OLAP Platform Helm charts.
*/}}

{{/*
Standard ClusterIP Service.
Usage: {{ include "common.service.clusterip" . }}
*/}}
{{- define "common.service.clusterip" -}}
apiVersion: v1
kind: Service
metadata:
  name: {{ include "common.names.fullname" . }}
  namespace: {{ include "common.names.namespace" . }}
  labels:
    {{- include "common.labels.standard" . | nindent 4 }}
  {{- with .Values.service.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  type: {{ .Values.service.type | default "ClusterIP" }}
  {{- if .Values.service.clusterIP }}
  clusterIP: {{ .Values.service.clusterIP }}
  {{- end }}
  ports:
    - name: http
      port: {{ .Values.service.port }}
      targetPort: {{ .Values.service.targetPort | default .Values.service.port }}
      protocol: TCP
    {{- if .Values.service.metricsPort }}
    - name: metrics
      port: {{ .Values.service.metricsPort }}
      targetPort: {{ .Values.service.metricsTargetPort | default .Values.service.metricsPort }}
      protocol: TCP
    {{- end }}
    {{- with .Values.service.extraPorts }}
    {{- toYaml . | nindent 4 }}
    {{- end }}
  selector:
    {{- include "common.labels.matchLabels" . | nindent 4 }}
{{- end }}

{{/*
Headless Service (for StatefulSets).
Usage: {{ include "common.service.headless" . }}
*/}}
{{- define "common.service.headless" -}}
apiVersion: v1
kind: Service
metadata:
  name: {{ include "common.names.fullname" . }}-headless
  namespace: {{ include "common.names.namespace" . }}
  labels:
    {{- include "common.labels.standard" . | nindent 4 }}
spec:
  type: ClusterIP
  clusterIP: None
  ports:
    - name: http
      port: {{ .Values.service.port }}
      targetPort: {{ .Values.service.targetPort | default .Values.service.port }}
      protocol: TCP
  selector:
    {{- include "common.labels.matchLabels" . | nindent 4 }}
{{- end }}

{{/*
Service ports block for deployment/statefulset pod template.
Usage: {{ include "common.service.containerPorts" . | nindent 12 }}
*/}}
{{- define "common.service.containerPorts" -}}
- name: http
  containerPort: {{ .Values.containerPort | default .Values.service.port }}
  protocol: TCP
{{- if .Values.metrics.enabled }}
- name: metrics
  containerPort: {{ .Values.metrics.port | default 9090 }}
  protocol: TCP
{{- end }}
{{- with .Values.extraContainerPorts }}
{{- toYaml . | nindent 0 }}
{{- end }}
{{- end }}
