{{/*
Affinity and anti-affinity templates for Graph OLAP Platform Helm charts.
*/}}

{{/*
Return a soft pod anti-affinity rule to spread pods across nodes.
Usage: {{ include "common.affinities.pods.soft" (dict "component" "control-plane" "context" $) | nindent 8 }}
*/}}
{{- define "common.affinities.pods.soft" -}}
podAntiAffinity:
  preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchLabels:
            app.kubernetes.io/name: {{ include "common.names.name" .context }}
            app.kubernetes.io/instance: {{ .context.Release.Name }}
            {{- if .component }}
            app.kubernetes.io/component: {{ .component }}
            {{- end }}
        topologyKey: kubernetes.io/hostname
{{- end }}

{{/*
Return a hard pod anti-affinity rule (one pod per node).
Usage: {{ include "common.affinities.pods.hard" (dict "component" "control-plane" "context" $) | nindent 8 }}
*/}}
{{- define "common.affinities.pods.hard" -}}
podAntiAffinity:
  requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchLabels:
          app.kubernetes.io/name: {{ include "common.names.name" .context }}
          app.kubernetes.io/instance: {{ .context.Release.Name }}
          {{- if .component }}
          app.kubernetes.io/component: {{ .component }}
          {{- end }}
      topologyKey: kubernetes.io/hostname
{{- end }}

{{/*
Return a zone-aware pod anti-affinity rule.
Usage: {{ include "common.affinities.pods.softZone" (dict "context" $) | nindent 8 }}
*/}}
{{- define "common.affinities.pods.softZone" -}}
podAntiAffinity:
  preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchLabels:
            app.kubernetes.io/name: {{ include "common.names.name" .context }}
            app.kubernetes.io/instance: {{ .context.Release.Name }}
        topologyKey: topology.kubernetes.io/zone
{{- end }}

{{/*
Return node affinity for specific node selector labels.
Usage: {{ include "common.affinities.nodes" (dict "nodeSelector" .Values.nodeSelector) | nindent 8 }}
*/}}
{{- define "common.affinities.nodes" -}}
{{- if .nodeSelector }}
nodeAffinity:
  requiredDuringSchedulingIgnoredDuringExecution:
    nodeSelectorTerms:
      - matchExpressions:
          {{- range $key, $value := .nodeSelector }}
          - key: {{ $key }}
            operator: In
            values:
              - {{ $value }}
          {{- end }}
{{- end }}
{{- end }}

{{/*
Return tolerations from values.
Usage: {{ include "common.affinities.tolerations" .Values.tolerations | nindent 8 }}
*/}}
{{- define "common.affinities.tolerations" -}}
{{- if . }}
{{- toYaml . }}
{{- end }}
{{- end }}

{{/*
Return node selector from values.
Usage: {{ include "common.affinities.nodeSelector" .Values.nodeSelector | nindent 8 }}
*/}}
{{- define "common.affinities.nodeSelector" -}}
{{- if . }}
{{- toYaml . }}
{{- end }}
{{- end }}

{{/*
Full affinity block combining pod anti-affinity and custom affinity.
Usage: {{ include "common.affinities.full" . | nindent 8 }}
*/}}
{{- define "common.affinities.full" -}}
{{- if .Values.affinity }}
{{- toYaml .Values.affinity }}
{{- else if .Values.podAntiAffinity }}
{{- if eq .Values.podAntiAffinity "soft" }}
{{ include "common.affinities.pods.soft" (dict "context" .) }}
{{- else if eq .Values.podAntiAffinity "hard" }}
{{ include "common.affinities.pods.hard" (dict "context" .) }}
{{- end }}
{{- end }}
{{- end }}
