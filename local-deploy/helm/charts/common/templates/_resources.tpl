{{/*
Resource-related templates for Graph OLAP Platform Helm charts.
*/}}

{{/*
Return resource requests and limits with defaults.
Usage: {{ include "common.resources.preset" (dict "resources" .Values.resources "defaults" .Values.defaultResources) | nindent 12 }}
*/}}
{{- define "common.resources.preset" -}}
{{- $defaults := .defaults | default dict }}
{{- $resources := .resources | default dict }}
{{- $merged := dict }}
{{- if or $resources.requests $defaults.requests }}
{{- $_ := set $merged "requests" (merge ($resources.requests | default dict) ($defaults.requests | default dict)) }}
{{- end }}
{{- if or $resources.limits $defaults.limits }}
{{- $_ := set $merged "limits" (merge ($resources.limits | default dict) ($defaults.limits | default dict)) }}
{{- end }}
{{- if $merged }}
{{- toYaml $merged }}
{{- end }}
{{- end }}

{{/*
Return resources as-is or empty.
Usage: {{ include "common.resources.standard" .Values.resources | nindent 12 }}
*/}}
{{- define "common.resources.standard" -}}
{{- if . }}
{{- toYaml . }}
{{- end }}
{{- end }}

{{/*
Validate that resource limits are set (for admission controllers).
Usage: {{ include "common.resources.validate" .Values.resources }}
*/}}
{{- define "common.resources.validate" -}}
{{- if not .limits }}
{{- fail "Resource limits are required (.Values.resources.limits)" }}
{{- end }}
{{- if not .limits.memory }}
{{- fail "Memory limit is required (.Values.resources.limits.memory)" }}
{{- end }}
{{- if not .limits.cpu }}
{{- fail "CPU limit is required (.Values.resources.limits.cpu)" }}
{{- end }}
{{- end }}
