{{/* Modified: 2026-02-08T15:00:00Z | Author: COPILOT | Change: Create Helm template helpers */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "slate.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "slate.fullname" -}}
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
*/}}
{{- define "slate.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "slate.labels" -}}
helm.sh/chart: {{ include "slate.chart" . }}
{{ include "slate.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: slate-system
{{- end }}

{{/*
Selector labels
*/}}
{{- define "slate.selectorLabels" -}}
app.kubernetes.io/name: {{ include "slate.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Pod security context
*/}}
{{- define "slate.podSecurityContext" -}}
runAsNonRoot: {{ .Values.security.podSecurityContext.runAsNonRoot }}
runAsUser: {{ .Values.security.podSecurityContext.runAsUser }}
runAsGroup: {{ .Values.security.podSecurityContext.runAsGroup }}
fsGroup: {{ .Values.security.podSecurityContext.fsGroup }}
seccompProfile:
  type: {{ .Values.security.podSecurityContext.seccompProfile.type }}
{{- end }}

{{/*
Container security context
*/}}
{{- define "slate.containerSecurityContext" -}}
allowPrivilegeEscalation: {{ .Values.security.containerSecurityContext.allowPrivilegeEscalation }}
readOnlyRootFilesystem: {{ .Values.security.containerSecurityContext.readOnlyRootFilesystem }}
capabilities:
  drop:
    {{- range .Values.security.containerSecurityContext.capabilities.drop }}
    - {{ . }}
    {{- end }}
{{- end }}

{{/*
GPU node selector and tolerations
*/}}
{{- define "slate.gpuNodeSelector" -}}
{{- if .Values.gpu.enabled }}
nodeSelector:
  {{- toYaml .Values.gpu.nodeSelector | nindent 2 }}
tolerations:
  {{- toYaml .Values.gpu.tolerations | nindent 2 }}
{{- end }}
{{- end }}
