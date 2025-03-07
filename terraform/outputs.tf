output "dataset_id" {
  description = "The ID of the created BigQuery dataset"
  value       = google_bigquery_dataset.tourism_analysis.dataset_id
}

output "raw_reviews_table" {
  description = "The ID of the raw reviews table"
  value       = google_bigquery_table.raw_reviews.table_id
}

output "reviews_for_ml_table" {
  description = "The ID of the reviews for ML table"
  value       = google_bigquery_table.reviews_for_ml.table_id
}

output "processed_reviews_table" {
  description = "The ID of the processed reviews table"
  value       = google_bigquery_table.processed_reviews.table_id
}

output "temp_bucket_name" {
  description = "The name of the temporary GCS bucket"
  value       = google_storage_bucket.temp_bucket.name
}

output "service_account_email" {
  description = "The email of the existing service account"
  value       = data.google_service_account.tourism_analysis_sa.email
}

output "service_account_key" {
  description = "The new service account key (base64 encoded)"
  value       = google_service_account_key.tourism_analysis_sa_key.private_key
  sensitive   = true
}

output "instructions" {
  description = "Next steps after applying Terraform"
  value       = <<EOF
  
================================================================================
Tourism Analysis Infrastructure has been created successfully!

Next steps:
1. Save the service account key to your secrets directory:
   [System.IO.File]::WriteAllText("..\secrets\service-account-tf.json", [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String((terraform output -raw service_account_key))))

2. Update your .env file with these values:
   GCP_PROJECT_ID=${var.project_id}
   BQ_DATASET_ID=${var.dataset_id}
   BQ_RAW_TABLE_ID=raw_reviews
   BQ_PROCESSED_TABLE_ID=reviews_for_ml
   TEMP_GCS_BUCKET=${google_storage_bucket.temp_bucket.name}

3. Restart your Docker services to apply these changes:
   docker-compose down
   docker-compose up -d
================================================================================
  
EOF
}