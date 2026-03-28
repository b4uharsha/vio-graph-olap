{{/*
Security context templates following NSA Kubernetes Hardening Guide
and Pod Security Standards (restricted profile).
*/}}

{{/*
Default restricted pod security context.
Usage: {{ include "common.security.podSecurityContext" . | nindent 8 }}
*/}}
{{- define "common.security.podSecurityContext" -}}
{{- $defaults := .Values.defaultSecurityContext.pod | default dict }}
{{- $overrides := .Values.podSecurityContext | default dict }}
{{- $merged := merge $overrides $defaults }}
{{- if $merged }}
{{- toYaml $merged }}
{{- else }}
runAsNonRoot: true
runAsUser: 65532
runAsGroup: 65532
fsGroup: 65532
seccompProfile:
  type: RuntimeDefault
{{- end }}
{{- end }}

{{/*
Default restricted container security context.
Usage: {{ include "common.security.containerSecurityContext" . | nindent 12 }}
*/}}
{{- define "common.security.containerSecurityContext" -}}
{{- $defaults := .Values.defaultSecurityContext.container | default dict }}
{{- $overrides := .Values.securityContext | default dict }}
{{- $merged := merge $overrides $defaults }}
{{- if $merged }}
{{- toYaml $merged }}
{{- else }}
allowPrivilegeEscalation: false
readOnlyRootFilesystem: true
capabilities:
  drop:
    - ALL
{{- end }}
{{- end }}

{{/*
Restricted pod security context (strictest settings).
Usage: {{ include "common.security.restrictedPodContext" . | nindent 8 }}
*/}}
{{- define "common.security.restrictedPodContext" -}}
runAsNonRoot: true
runAsUser: 65532
runAsGroup: 65532
fsGroup: 65532
fsGroupChangePolicy: OnRootMismatch
seccompProfile:
  type: RuntimeDefault
{{- end }}

{{/*
Restricted container security context (strictest settings).
Usage: {{ include "common.security.restrictedContainerContext" . | nindent 12 }}
*/}}
{{- define "common.security.restrictedContainerContext" -}}
allowPrivilegeEscalation: false
readOnlyRootFilesystem: true
runAsNonRoot: true
runAsUser: 65532
runAsGroup: 65532
capabilities:
  drop:
    - ALL
seccompProfile:
  type: RuntimeDefault
{{- end }}

{{/*
Relaxed container security context for containers that need writable filesystem.
Usage: {{ include "common.security.relaxedContainerContext" . | nindent 12 }}
*/}}
{{- define "common.security.relaxedContainerContext" -}}
allowPrivilegeEscalation: false
readOnlyRootFilesystem: false
runAsNonRoot: true
runAsUser: 65532
runAsGroup: 65532
capabilities:
  drop:
    - ALL
seccompProfile:
  type: RuntimeDefault
{{- end }}
