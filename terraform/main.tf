terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.75.0"
    }
  }
}
provider "google" {
  project = var.project_id
  region  = var.region
}


resource "google_storage_bucket" "temp_bucket" {
  name          = "${var.project_id}-${var.temp_bucket_name}"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true
}

resource "google_bigquery_dataset" "tourism_analysis" {
  dataset_id    = "${var.dataset_id}"
  friendly_name = "Tourism Reviews Analysis"
  description   = "Dataset for storing and analyzing tourism reviews"
  location      = var.bigquery_location

  default_table_expiration_ms = 2592000000 
}


resource "google_bigquery_table" "raw_reviews" {
  dataset_id = google_bigquery_dataset.tourism_analysis.dataset_id
  table_id   = "raw_reviews"

  schema = <<EOF
[
  {
    "name": "review_id",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "username",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "product",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "category",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "location",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "rating",
    "type": "INTEGER",
    "mode": "NULLABLE"
  },
  {
    "name": "review_text",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "original_sentiment_bias",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "created_at",
    "type": "TIMESTAMP",
    "mode": "NULLABLE"
  },
  {
    "name": "ingested_at",
    "type": "TIMESTAMP",
    "mode": "NULLABLE"
  }
]
EOF
}


resource "google_bigquery_table" "reviews_for_ml" {
  dataset_id = google_bigquery_dataset.tourism_analysis.dataset_id
  table_id   = "reviews_for_ml"

  schema = <<EOF
[
  {
    "name": "review_id",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "username",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "product",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "category",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "location",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "rating",
    "type": "INTEGER",
    "mode": "NULLABLE"
  },
  {
    "name": "review_text",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "sentiment_bias",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "timestamp",
    "type": "TIMESTAMP",
    "mode": "NULLABLE"
  },
  {
    "name": "review_length",
    "type": "INTEGER",
    "mode": "NULLABLE"
  },
  {
    "name": "processed_at",
    "type": "TIMESTAMP",
    "mode": "NULLABLE"
  }
]
EOF
}


resource "google_bigquery_table" "processed_reviews" {
  dataset_id = google_bigquery_dataset.tourism_analysis.dataset_id
  table_id   = "processed_reviews"

  schema = <<EOF
[
  {
    "name": "review_id",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "username",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "product",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "category",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "location",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "rating",
    "type": "INTEGER",
    "mode": "NULLABLE"
  },
  {
    "name": "review_text",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "sentiment_bias",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "timestamp",
    "type": "TIMESTAMP",
    "mode": "NULLABLE"
  },
  {
    "name": "review_length",
    "type": "INTEGER",
    "mode": "NULLABLE"
  },
  {
    "name": "processed_at",
    "type": "TIMESTAMP",
    "mode": "NULLABLE"
  },
  {
    "name": "predicted_sentiment_bias",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "sentiment_category",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "sentiment_score",
    "type": "FLOAT",
    "mode": "NULLABLE"
  },
  {
    "name": "sentiment_match",
    "type": "BOOLEAN",
    "mode": "NULLABLE"
  }
]
EOF
}

data "google_service_account" "tourism_analysis_sa" {
  account_id = var.service_account_id
}















resource "google_service_account_key" "tourism_analysis_sa_key" {
  service_account_id = data.google_service_account.tourism_analysis_sa.name
}

