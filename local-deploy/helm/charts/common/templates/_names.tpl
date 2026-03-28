{{/*
Common name templates for Graph OLAP Platform Helm charts.
These templates provide standardized naming conventions across all charts.
*/}}

{{/*
Expand the name of the chart.
Usage: {{ include "common.names.name" . }}
*/}}
{{- define "common.names.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
Usage: {{ include "common.names.fullname" . }}
*/}}
{{- define "common.names.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
Usage: {{ include "common.names.chart" . }}
*/}}
{{- define "common.names.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create the name of the service account to use.
Usage: {{ include "common.names.serviceAccountName" . }}
*/}}
{{- define "common.names.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "common.names.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create a name for a component resource (e.g., deployment-web, service-api).
Usage: {{ include "common.names.component" (dict "root" . "component" "web") }}
*/}}
{{- define "common.names.component" -}}
{{- printf "%s-%s" (include "common.names.fullname" .root) .component | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Kubernetes standard namespace.
Usage: {{ include "common.names.namespace" . }}
*/}}
{{- define "common.names.namespace" -}}
{{- default .Release.Namespace .Values.namespaceOverride }}
{{- end }}
