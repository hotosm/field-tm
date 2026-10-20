{{/*
Expand the name of the chart.
*/}}
{{- define "field-tm.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "field-tm.fullname" -}}
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
{{- define "field-tm.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "field-tm.labels" -}}
helm.sh/chart: {{ include "field-tm.chart" . }}
{{ include "field-tm.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "field-tm.selectorLabels" -}}
app.kubernetes.io/name: {{ include "field-tm.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "field-tm.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "field-tm.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Database service name.
*/}}
{{- define "field-tm.dbServiceName" -}}
{{- printf "%s-db" .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{/*
Database service DNS name inside the cluster.
*/}}
{{- define "field-tm.dbServiceHost" -}}
{{- printf "%s.%s.svc.cluster.local" (include "field-tm.dbServiceName" .) .Release.Namespace -}}
{{- end }}

{{/*
Database connection env (FTM_DB_*) for the in-cluster db.
With an external db these come from existingSecret instead.
*/}}
{{- define "field-tm.dbEnv" -}}
{{- if .Values.db.enabled }}
- name: FTM_DB_HOST
  value: {{ include "field-tm.dbServiceHost" . | quote }}
- name: FTM_DB_USER
  value: {{ .Values.db.auth.username | quote }}
- name: FTM_DB_PASSWORD
  value: {{ .Values.db.auth.password | quote }}
- name: FTM_DB_NAME
  value: {{ .Values.db.auth.database | quote }}
{{- end }}
{{- end }}

{{/*
Auth and monitoring env for the backend container.
*/}}
{{- define "field-tm.authEnv" -}}
{{- $provider := .Values.auth.provider | default "hotosm" -}}
{{- if not (has $provider (list "hotosm" "bundled" "custom" "disabled")) -}}
{{- fail (printf "auth.provider must be one of hotosm, bundled, custom, disabled (got %q)" $provider) -}}
{{- end }}
- name: AUTH_PROVIDER
  value: {{ $provider | quote }}
{{- if has $provider (list "bundled" "custom") }}
- name: HANKO_API_URL
  value: {{ required (printf "auth.hankoApiUrl is required when auth.provider=%s" $provider) .Values.auth.hankoApiUrl | quote }}
{{- end }}
{{- if eq $provider "custom" }}
- name: LOGIN_URL
  value: {{ required "auth.loginUrl is required when auth.provider=custom" .Values.auth.loginUrl | quote }}
{{- end }}
{{- if or .Values.sentry.dsn .Values.sentry.existingSecret }}
- name: MONITORING
  value: sentry
- name: SENTRY_DSN
  {{- if .Values.sentry.existingSecret }}
  valueFrom:
    secretKeyRef:
      name: {{ .Values.sentry.existingSecret | quote }}
      key: SENTRY_DSN
  {{- else }}
  value: {{ .Values.sentry.dsn | quote }}
  {{- end }}
{{- end }}
{{- end }}
