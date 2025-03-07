
resource "google_bigquery_data_transfer_config" "sentiment_model_training" {
  display_name           = "Sentiment Model Training"
  data_source_id         = "scheduled_query"
  schedule               = "every 24 hours"
  destination_dataset_id = google_bigquery_dataset.tourism_analysis.dataset_id
  location               = var.bigquery_location
  
  params = {
    query = <<EOF
CREATE OR REPLACE MODEL `${var.project_id}.${var.dataset_id}.sentiment_model`
OPTIONS(
  model_type='LOGISTIC_REG',
  input_label_cols=['sentiment_bias'],
  max_iterations=20
) AS
SELECT
  review_text,
  rating,
  review_length,
  sentiment_bias
FROM
  `${var.project_id}.${var.dataset_id}.reviews_for_ml`
WHERE
  sentiment_bias IN ('positive', 'negative', 'neutral');
EOF
  }

  service_account_name = data.google_service_account.tourism_analysis_sa.email
  
}


resource "google_bigquery_data_transfer_config" "sentiment_prediction" {
  display_name           = "Process Reviews with ML"
  data_source_id         = "scheduled_query"
  schedule               = "every 1 hours"
  destination_dataset_id = google_bigquery_dataset.tourism_analysis.dataset_id
  location               = var.bigquery_location
  
  params = {
    query = <<EOF
CREATE OR REPLACE TABLE `${var.project_id}.${var.dataset_id}.processed_reviews` AS
WITH predictions AS (
  SELECT
    r.*,
    ml.predicted_sentiment_bias,
    ml.probs
  FROM
    `${var.project_id}.${var.dataset_id}.reviews_for_ml` r,
    ML.PREDICT(MODEL `${var.project_id}.${var.dataset_id}.sentiment_model`,
      SELECT 
        review_id,
        review_text,
        rating,
        review_length
      FROM `${var.project_id}.${var.dataset_id}.reviews_for_ml`
    ) ml
  WHERE r.review_id = ml.review_id
)
SELECT
  p.*,
  CASE
    WHEN p.probs[OFFSET(0)].prob > 0.7 THEN 'very negative'
    WHEN p.probs[OFFSET(0)].prob > 0.5 THEN 'negative'
    WHEN p.probs[OFFSET(1)].prob > 0.7 THEN 'very positive'
    WHEN p.probs[OFFSET(1)].prob > 0.5 THEN 'positive'
    ELSE 'neutral'
  END AS sentiment_category,
  p.probs[OFFSET(1)].prob - p.probs[OFFSET(0)].prob AS sentiment_score,
  p.sentiment_bias = p.predicted_sentiment_bias AS sentiment_match
FROM
  predictions p;
EOF
  }

  service_account_name = data.google_service_account.tourism_analysis_sa.email
  
  depends_on = [
    google_bigquery_data_transfer_config.sentiment_model_training
  ]
}


resource "google_bigquery_table" "sentiment_analytics_view" {
  dataset_id = google_bigquery_dataset.tourism_analysis.dataset_id
  table_id   = "sentiment_analytics"
  
  view {
    query = <<EOF
SELECT
  r.category,
  r.rating,
  r.sentiment_category,
  r.sentiment_score,
  r.sentiment_match,
  r.location,
  r.product,
  r.review_length,
  DATE(r.timestamp) as review_date,
  EXTRACT(DAYOFWEEK FROM r.timestamp) as day_of_week,
  EXTRACT(HOUR FROM r.timestamp) as hour_of_day,
  COUNT(*) as review_count
FROM
  `${var.project_id}.${var.dataset_id}.processed_reviews` r
GROUP BY
  category, rating, sentiment_category, sentiment_score, 
  sentiment_match, location, product, review_length,
  review_date, day_of_week, hour_of_day
EOF
    use_legacy_sql = false
  }

  depends_on = [
    google_bigquery_table.processed_reviews
  ]
}