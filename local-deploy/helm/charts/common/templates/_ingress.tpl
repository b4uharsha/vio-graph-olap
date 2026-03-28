{{/*
Ingress templates for Graph OLAP Platform Helm charts.
*/}}

{{/*
Standard Ingress resource.
Usage: {{ include "common.ingress" . }}
*/}}
{{- define "common.ingress" -}}
{{- if .Values.ingress.enabled -}}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "common.names.fullname" . }}
  namespace: {{ include "common.names.namespace" . }}
  labels:
    {{- include "common.labels.standard" . | nindent 4 }}
  {{- with .Values.ingress.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  {{- if .Values.ingress.className }}
  ingressClassName: {{ .Values.ingress.className }}
  {{- end }}
  {{- if .Values.ingress.tls }}
  tls:
    {{- range .Values.ingress.tls }}
    - hosts:
        {{- range .hosts }}
        - {{ . | quote }}
        {{- end }}
      secretName: {{ .secretName }}
    {{- end }}
  {{- end }}
  rules:
    {{- range .Values.ingress.hosts }}
    - host: {{ .host | quote }}
      http:
        paths:
          {{- range .paths }}
          - path: {{ .path }}
            pathType: {{ .pathType | default "Prefix" }}
            backend:
              service:
                name: {{ include "common.names.fullname" $ }}
                port:
                  number: {{ $.Values.service.port }}
          {{- end }}
    {{- end }}
{{- end }}
{{- end }}

{{/*
GKE Internal Ingress annotations.
Usage: {{ include "common.ingress.gkeInternalAnnotations" . | nindent 4 }}
*/}}
{{- define "common.ingress.gkeInternalAnnotations" -}}
kubernetes.io/ingress.class: "gce-internal"
kubernetes.io/ingress.regional-static-ip-name: {{ .Values.ingress.staticIPName | quote }}
{{- if .Values.ingress.backendConfig }}
cloud.google.com/backend-config: '{"default": "{{ include "common.names.fullname" . }}"}'
{{- end }}
{{- end }}

{{/*
GKE External Ingress annotations with managed certificate.
Usage: {{ include "common.ingress.gkeExternalAnnotations" . | nindent 4 }}
*/}}
{{- define "common.ingress.gkeExternalAnnotations" -}}
kubernetes.io/ingress.class: "gce"
kubernetes.io/ingress.global-static-ip-name: {{ .Values.ingress.staticIPName | quote }}
{{- if .Values.ingress.managedCertificate }}
networking.gke.io/managed-certificates: {{ .Values.ingress.managedCertificate | quote }}
{{- end }}
{{- end }}
