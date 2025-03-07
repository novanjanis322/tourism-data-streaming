import os
import time
import json
import logging
import uuid
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, length, current_timestamp, to_timestamp
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType
from google.cloud import bigquery
from google.oauth2 import service_account

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
KAFKA_TOPIC = os.environ.get('KAFKA_TOPIC', 'tourism_reviews')
PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
DATASET_ID = os.environ.get('BQ_DATASET_ID', 'tourism')
PROCESSED_TABLE_ID = os.environ.get('BQ_PROCESSED_TABLE_ID', 'reviews_for_ml')
SERVICE_ACCOUNT_PATH = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '/secrets/service-account.json')
MAX_RETRIES = 5  
RETRY_INTERVAL = 60  

def get_bigquery_client():
    """Create and return a BigQuery client."""
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_PATH,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    
    return bigquery.Client(
        credentials=credentials,
        project=PROJECT_ID,
    )

def create_table_if_not_exists():
    """Create the BigQuery table if it doesn't exist."""
    client = get_bigquery_client()
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{PROCESSED_TABLE_ID}"
    
    try:
        client.get_table(table_id)
        logger.info(f"Table {table_id} already exists")
    except Exception:
        
        schema = [
            bigquery.SchemaField("review_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("username", "STRING"),
            bigquery.SchemaField("product", "STRING"),
            bigquery.SchemaField("category", "STRING"),
            bigquery.SchemaField("location", "STRING"),
            bigquery.SchemaField("rating", "INTEGER"),
            bigquery.SchemaField("review_text", "STRING"),
            bigquery.SchemaField("sentiment_bias", "STRING"),
            bigquery.SchemaField("timestamp", "TIMESTAMP"),
            bigquery.SchemaField("review_length", "INTEGER"),
            bigquery.SchemaField("processed_at", "TIMESTAMP")
        ]
        
        
        table = bigquery.Table(table_id, schema=schema)
        table = client.create_table(table)
        logger.info(f"Created table {table_id}")

def process_batch(df, epoch_id):
    """Process each batch of data and write directly to BigQuery."""
    logger.info(f"Processing batch: {epoch_id}")
    
    try:
        count = df.count()
        if count == 0:
            logger.info("Empty batch, skipping...")
            return
        
        logger.info(f"Batch contains {count} records")
        
        
        processed_df = df.withColumn("timestamp", to_timestamp(col("timestamp")))
        
        
        rows = processed_df.toJSON().collect()
        rows = [json.loads(row) for row in rows]
        
        
        client = get_bigquery_client()
        
        
        table_id = f"{PROJECT_ID}.{DATASET_ID}.{PROCESSED_TABLE_ID}"
        errors = client.insert_rows_json(table_id, rows)
        
        if errors:
            logger.error(f"Errors inserting rows into BigQuery: {errors}")
        else:
            logger.info(f"Successfully inserted {len(rows)} rows into BigQuery")
            
    except Exception as e:
        logger.error(f"Error processing batch {epoch_id}: {e}")
        

def create_spark_session():
    """Create a Spark session with proper configuration."""
    
    return SparkSession.builder \
        .appName("Tourism Reviews Processor") \
        .config("spark.driver.extraClassPath", "/opt/spark/jars/*") \
        .config("spark.executor.extraClassPath", "/opt/spark/jars/*") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0") \
        .getOrCreate()

def initialize_streaming_query(spark):
    """Initialize the streaming query with retry logic."""
    schema = StructType([
        StructField("review_id", StringType()),
        StructField("username", StringType()),
        StructField("product", StringType()),
        StructField("category", StringType()),
        StructField("location", StringType()),
        StructField("rating", IntegerType()),
        StructField("review_text", StringType()),
        StructField("sentiment_bias", StringType()),
        StructField("timestamp", StringType())
    ])
    
    logger.info(f"Connecting to Kafka at {KAFKA_BOOTSTRAP_SERVERS}, topic: {KAFKA_TOPIC}")
    
    
    checkpoint_location = f"/tmp/checkpoints/{str(uuid.uuid4())}"
    os.makedirs(checkpoint_location, exist_ok=True)
    
    
    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", KAFKA_TOPIC) \
        .option("startingOffsets", "latest") \
        .option("failOnDataLoss", "false") \
        .load()
    
    
    parsed_df = df \
        .selectExpr("CAST(value AS STRING) as json") \
        .select(from_json("json", schema).alias("data")) \
        .select("data.*") \
        .withColumn("review_length", length(col("review_text"))) \
        .withColumn("processed_at", current_timestamp())
    
    
    logger.info("Setting up foreachBatch processing")
    query = parsed_df \
        .writeStream \
        .foreachBatch(process_batch) \
        .option("checkpointLocation", checkpoint_location) \
        .trigger(processingTime="20 seconds") \
        .start()
    
    logger.info("Stream processing started")
    return query

def main_loop():
    """Main function with exactly 5 retries and 60-second intervals."""
    
    create_table_if_not_exists()
    
    retries = 0
    while retries < MAX_RETRIES:  
        try:
            
            spark = create_spark_session()
            spark.sparkContext.setLogLevel("WARN")
            
            
            query = initialize_streaming_query(spark)
            
            
            query.awaitTermination()
            
            
            break
            
        except Exception as e:
            retries += 1
            logger.error(f"Error in streaming job (attempt {retries}/{MAX_RETRIES}): {e}")
            
            if retries < MAX_RETRIES:
                logger.info(f"Retrying in {RETRY_INTERVAL} seconds...")
                time.sleep(RETRY_INTERVAL)
            else:
                logger.error("Maximum retries reached, exiting...")
                break  

if __name__ == "__main__":
    
    initial_wait = 60  
    logger.info(f"Waiting {initial_wait} seconds for Kafka to be ready...")
    time.sleep(initial_wait)
    
    try:
        
        main_loop()
    except KeyboardInterrupt:
        logger.info("Processor stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")