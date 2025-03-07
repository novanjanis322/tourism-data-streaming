import json
import os
import time
import logging
from datetime import datetime
from kafka import KafkaConsumer
from google.cloud import bigquery
from google.oauth2 import service_account


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
DATASET_ID = os.environ.get('BQ_DATASET_ID', 'sentiment_analysis')
RAW_TABLE_ID = os.environ.get('BQ_RAW_TABLE_ID', 'raw_reviews')
SERVICE_ACCOUNT_PATH = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '/secrets/service-account.json')


KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
KAFKA_TOPIC = os.environ.get('KAFKA_TOPIC', 'tourism_reviews')
KAFKA_GROUP_ID = os.environ.get('KAFKA_GROUP_ID', 'sentiment_analysis_group')

def create_bigquery_client():
    """Create and return a BigQuery client."""
    for attempt in range(1, 6):
        try:
            logger.info(f"Attempting to connect to BigQuery (attempt {attempt})...")
            
            
            if not os.path.exists(SERVICE_ACCOUNT_PATH):
                logger.error(f"Service account file not found at: {SERVICE_ACCOUNT_PATH}")
                raise FileNotFoundError(f"Service account file not found at: {SERVICE_ACCOUNT_PATH}")
            
            
            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_PATH,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            
            
            client = bigquery.Client(
                credentials=credentials,
                project=PROJECT_ID,
            )
            
            logger.info("Successfully connected to BigQuery")
            return client
        except Exception as e:
            logger.error(f"BigQuery connection attempt {attempt} failed: {e}")
            if attempt < 5:
                sleep_time = 2 ** attempt  
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                logger.error("All BigQuery connection attempts failed")
                raise

def create_dataset_and_table(client):
    """Create BigQuery dataset and raw table if they don't exist."""
    try:
        
        dataset_ref = client.dataset(DATASET_ID)
        try:
            client.get_dataset(dataset_ref)
            logger.info(f"Dataset {DATASET_ID} already exists")
        except Exception:
            
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "asia-southeast2"  
            dataset = client.create_dataset(dataset)
            logger.info(f"Dataset {DATASET_ID} created")
        
        
        raw_schema = [
            bigquery.SchemaField("review_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("username", "STRING"),
            bigquery.SchemaField("product", "STRING"),
            bigquery.SchemaField("category", "STRING"),
            bigquery.SchemaField("location", "STRING"),
            bigquery.SchemaField("rating", "INTEGER"),
            bigquery.SchemaField("review_text", "STRING"),
            bigquery.SchemaField("original_sentiment_bias", "STRING"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
            bigquery.SchemaField("ingested_at", "TIMESTAMP"),
        ]
        
        
        raw_table_ref = dataset_ref.table(RAW_TABLE_ID)
        try:
            client.get_table(raw_table_ref)
            logger.info(f"Table {RAW_TABLE_ID} already exists")
        except Exception:
            
            raw_table = bigquery.Table(raw_table_ref, schema=raw_schema)
            raw_table = client.create_table(raw_table)
            logger.info(f"Table {RAW_TABLE_ID} created")
            
    except Exception as e:
        logger.error(f"Error setting up BigQuery: {e}")
        raise

def insert_to_bigquery(client, rows):
    """Insert raw review data into BigQuery table."""
    if not rows:
        return
    
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{RAW_TABLE_ID}"
    
    
    errors = client.insert_rows_json(table_ref, rows)
    
    if errors:
        logger.error(f"Errors inserting rows into BigQuery: {errors}")
    else:
        logger.info(f"Successfully inserted {len(rows)} rows into BigQuery")

def create_consumer():
    """Create and return a Kafka consumer."""
    for attempt in range(1, 6):
        try:
            logger.info(f"Attempting to connect to Kafka (attempt {attempt})...")
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
                group_id=KAFKA_GROUP_ID,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=False,
                max_poll_interval_ms=300000,  
                max_poll_records=100
            )
            logger.info("Successfully connected to Kafka")
            return consumer
        except Exception as e:
            logger.error(f"Kafka consumer connection attempt {attempt} failed: {e}")
            if attempt < 5:
                sleep_time = 2 ** attempt  
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                logger.error("All Kafka consumer connection attempts failed")
                raise

def run_consumer():
    """Main function to run the Kafka consumer."""
    try:
        
        bq_client = create_bigquery_client()
        
        
        create_dataset_and_table(bq_client)
        
        
        consumer = create_consumer()
        
        
        buffer = []
        buffer_size = 10  
        buffer_time = time.time()  
        max_buffer_time = 60  
        
        logger.info(f"Starting to consume messages from topic '{KAFKA_TOPIC}'...")
        
        for message in consumer:
            try:
                
                review_data = message.value
                
                
                bq_row = {
                    'review_id': review_data['review_id'],
                    'username': review_data['username'],
                    'product': review_data['product'],
                    'category': review_data['category'],
                    'location': review_data.get('location', 'Unknown'),
                    'rating': review_data['rating'],
                    'review_text': review_data['review_text'],
                    'original_sentiment_bias': review_data.get('sentiment_bias', 'unknown'),
                    'created_at': review_data['timestamp'],
                    'ingested_at': datetime.now().isoformat()
                }
                
                
                buffer.append(bq_row)
                
                
                current_time = time.time()
                if len(buffer) >= buffer_size or (current_time - buffer_time) > max_buffer_time:
                    insert_to_bigquery(bq_client, buffer)
                    buffer = []  
                    buffer_time = current_time  
                    consumer.commit()  
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                
    except KeyboardInterrupt:
        logger.info("Consumer stopped by user")
    except Exception as e:
        logger.error(f"Error in consumer: {e}")
    finally:
        logger.info("Closing consumer")
        if 'consumer' in locals():
            consumer.close()

if __name__ == "__main__":
    run_consumer()