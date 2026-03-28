{{/*
Image-related templates for Graph OLAP Platform Helm charts.
*/}}

{{/*
Return the proper image name with registry prefix.
Usage: {{ include "common.images.image" (dict "imageRoot" .Values.image "global" .Values.global) }}
*/}}
{{- define "common.images.image" -}}
{{- $registryName := .imageRoot.registry | default .global.imageRegistry | default "" -}}
{{- $repositoryName := .imageRoot.repository -}}
{{- $separator := ":" -}}
{{- $termination := .imageRoot.tag | default .Chart.AppVersion | toString -}}
{{- if .imageRoot.digest }}
    {{- $separator = "@" -}}
    {{- $termination = .imageRoot.digest | toString -}}
{{- end -}}
{{- if $registryName }}
    {{- printf "%s/%s%s%s" $registryName $repositoryName $separator $termination -}}
{{- else -}}
    {{- printf "%s%s%s" $repositoryName $separator $termination -}}
{{- end -}}
{{- end -}}

{{/*
Return the proper image pull policy.
Usage: {{ include "common.images.pullPolicy" (dict "imageRoot" .Values.image "global" .Values.global) }}
*/}}
{{- define "common.images.pullPolicy" -}}
{{- $pullPolicy := .imageRoot.pullPolicy | default "IfNotPresent" -}}
{{- if eq $pullPolicy "latest" }}
    {{- print "Always" -}}
{{- else -}}
    {{- print $pullPolicy -}}
{{- end -}}
{{- end -}}

{{/*
Return the proper image pull secrets.
Usage: {{ include "common.images.pullSecrets" (dict "images" (list .Values.image) "global" .Values.global) }}
*/}}
{{- define "common.images.pullSecrets" -}}
{{- $pullSecrets := list }}
{{- if .global }}
  {{- range .global.imagePullSecrets }}
    {{- if kindIs "map" . }}
      {{- $pullSecrets = append $pullSecrets .name }}
    {{- else }}
      {{- $pullSecrets = append $pullSecrets . }}
    {{- end }}
  {{- end }}
{{- end }}
{{- range .images }}
  {{- if .pullSecrets }}
    {{- range .pullSecrets }}
      {{- if kindIs "map" . }}
        {{- $pullSecrets = append $pullSecrets .name }}
      {{- else }}
        {{- $pullSecrets = append $pullSecrets . }}
      {{- end }}
    {{- end }}
  {{- end }}
{{- end }}
{{- if (not (empty $pullSecrets)) }}
imagePullSecrets:
  {{- range $pullSecrets | uniq }}
  - name: {{ . }}
  {{- end }}
{{- end }}
{{- end -}}

{{/*
Simple image string with tag.
Usage: {{ include "common.images.simple" . }}
Expects .Values.image with repository, tag, pullPolicy
*/}}
{{- define "common.images.simple" -}}
{{- $registry := .Values.image.registry | default .Values.global.imageRegistry | default "" -}}
{{- $repo := .Values.image.repository -}}
{{- $tag := .Values.image.tag | default .Chart.AppVersion -}}
{{- if $registry -}}
{{ $registry }}/{{ $repo }}:{{ $tag }}
{{- else -}}
{{ $repo }}:{{ $tag }}
{{- end -}}
{{- end -}}
