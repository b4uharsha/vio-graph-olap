{{/*
Health probe templates for Graph OLAP Platform Helm charts.
*/}}

{{/*
HTTP liveness probe.
Usage: {{ include "common.probes.liveness.http" (dict "path" "/health" "port" 8000 "config" .Values.livenessProbe) | nindent 12 }}
*/}}
{{- define "common.probes.liveness.http" -}}
{{- $defaults := dict "initialDelaySeconds" 10 "periodSeconds" 10 "timeoutSeconds" 5 "failureThreshold" 3 "successThreshold" 1 }}
{{- $config := merge (.config | default dict) $defaults }}
httpGet:
  path: {{ .path | default "/health" }}
  port: {{ .port | default 8000 }}
  {{- if .scheme }}
  scheme: {{ .scheme }}
  {{- end }}
initialDelaySeconds: {{ $config.initialDelaySeconds }}
periodSeconds: {{ $config.periodSeconds }}
timeoutSeconds: {{ $config.timeoutSeconds }}
failureThreshold: {{ $config.failureThreshold }}
successThreshold: {{ $config.successThreshold }}
{{- end }}

{{/*
HTTP readiness probe.
Usage: {{ include "common.probes.readiness.http" (dict "path" "/health" "port" 8000 "config" .Values.readinessProbe) | nindent 12 }}
*/}}
{{- define "common.probes.readiness.http" -}}
{{- $defaults := dict "initialDelaySeconds" 5 "periodSeconds" 5 "timeoutSeconds" 3 "failureThreshold" 3 "successThreshold" 1 }}
{{- $config := merge (.config | default dict) $defaults }}
httpGet:
  path: {{ .path | default "/health" }}
  port: {{ .port | default 8000 }}
  {{- if .scheme }}
  scheme: {{ .scheme }}
  {{- end }}
initialDelaySeconds: {{ $config.initialDelaySeconds }}
periodSeconds: {{ $config.periodSeconds }}
timeoutSeconds: {{ $config.timeoutSeconds }}
failureThreshold: {{ $config.failureThreshold }}
successThreshold: {{ $config.successThreshold }}
{{- end }}

{{/*
HTTP startup probe (for slow-starting containers).
Usage: {{ include "common.probes.startup.http" (dict "path" "/health" "port" 8000 "config" .Values.startupProbe) | nindent 12 }}
*/}}
{{- define "common.probes.startup.http" -}}
{{- $defaults := dict "initialDelaySeconds" 0 "periodSeconds" 10 "timeoutSeconds" 5 "failureThreshold" 30 "successThreshold" 1 }}
{{- $config := merge (.config | default dict) $defaults }}
httpGet:
  path: {{ .path | default "/health" }}
  port: {{ .port | default 8000 }}
  {{- if .scheme }}
  scheme: {{ .scheme }}
  {{- end }}
initialDelaySeconds: {{ $config.initialDelaySeconds }}
periodSeconds: {{ $config.periodSeconds }}
timeoutSeconds: {{ $config.timeoutSeconds }}
failureThreshold: {{ $config.failureThreshold }}
successThreshold: {{ $config.successThreshold }}
{{- end }}

{{/*
TCP liveness probe.
Usage: {{ include "common.probes.liveness.tcp" (dict "port" 8000 "config" .Values.livenessProbe) | nindent 12 }}
*/}}
{{- define "common.probes.liveness.tcp" -}}
{{- $defaults := dict "initialDelaySeconds" 10 "periodSeconds" 10 "timeoutSeconds" 5 "failureThreshold" 3 "successThreshold" 1 }}
{{- $config := merge (.config | default dict) $defaults }}
tcpSocket:
  port: {{ .port | default 8000 }}
initialDelaySeconds: {{ $config.initialDelaySeconds }}
periodSeconds: {{ $config.periodSeconds }}
timeoutSeconds: {{ $config.timeoutSeconds }}
failureThreshold: {{ $config.failureThreshold }}
successThreshold: {{ $config.successThreshold }}
{{- end }}

{{/*
Exec liveness probe (for custom health checks).
Usage: {{ include "common.probes.liveness.exec" (dict "command" (list "/bin/sh" "-c" "curl localhost") "config" .Values.livenessProbe) | nindent 12 }}
*/}}
{{- define "common.probes.liveness.exec" -}}
{{- $defaults := dict "initialDelaySeconds" 10 "periodSeconds" 10 "timeoutSeconds" 5 "failureThreshold" 3 "successThreshold" 1 }}
{{- $config := merge (.config | default dict) $defaults }}
exec:
  command:
    {{- toYaml .command | nindent 4 }}
initialDelaySeconds: {{ $config.initialDelaySeconds }}
periodSeconds: {{ $config.periodSeconds }}
timeoutSeconds: {{ $config.timeoutSeconds }}
failureThreshold: {{ $config.failureThreshold }}
successThreshold: {{ $config.successThreshold }}
{{- end }}

{{/*
Generic probe from values (pass-through).
Usage: {{ include "common.probes.fromValues" .Values.livenessProbe | nindent 12 }}
*/}}
{{- define "common.probes.fromValues" -}}
{{- if . }}
{{- toYaml . }}
{{- end }}
{{- end }}
