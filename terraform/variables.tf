variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud region for resources"
  type        = string
}

variable "bigquery_location" {
  description = "Location for BigQuery resources"
  type        = string
}

variable "dataset_id" {
  description = "BigQuery dataset ID"
  type        = string
}

variable "temp_bucket_name" {
  description = "Name for the temporary GCS bucket"
  type        = string
}

variable "service_account_id" {
  description = "ID of the existing service account to use"
  type        = string
}