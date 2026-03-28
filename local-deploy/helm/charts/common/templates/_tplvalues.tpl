{{/*
Utility templates for rendering values as templates.
*/}}

{{/*
Renders a value that contains template.
Usage: {{ include "common.tplvalues.render" (dict "value" .Values.path.to.value "context" $) }}
*/}}
{{- define "common.tplvalues.render" -}}
{{- if typeIs "string" .value }}
  {{- tpl .value .context }}
{{- else }}
  {{- tpl (.value | toYaml) .context }}
{{- end }}
{{- end }}

{{/*
Merge multiple values and render as YAML.
Usage: {{ include "common.tplvalues.merge" (dict "values" (list .Values.a .Values.b) "context" $) }}
*/}}
{{- define "common.tplvalues.merge" -}}
{{- $merged := dict }}
{{- range .values }}
  {{- $merged = merge $merged . }}
{{- end }}
{{- toYaml $merged }}
{{- end }}

{{/*
Get a value with a default.
Usage: {{ include "common.tplvalues.default" (dict "value" .Values.key "default" "fallback") }}
*/}}
{{- define "common.tplvalues.default" -}}
{{- if .value }}
{{- .value }}
{{- else }}
{{- .default }}
{{- end }}
{{- end }}
