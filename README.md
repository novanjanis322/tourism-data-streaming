# Sentiment Analysis Streaming Project

## Overview

This project implements a real-time sentiment analysis pipeline for streaming data. The pipeline collects, processes, and stores streaming review data to perform sentiment analysis using multiple components and cloud-based infrastructure.

## Architecture

The system works as follows:

+------------+       +--------+       +------------+       +------------------+
|  Producer  | ----> | Kafka  | ----> |  Consumer  | ----> | BigQuery (Raw Data) |
+------------+       +--------+       +------------+       +------------------+
                                                           |
                                                           v
                                           +------------------------+
                                           | Spark Processor        |
                                           | (Data Processing)      |
                                           +------------------------+
                                                           |
                                                           v
                                           +-------------------------------+
                                           | BigQuery (Processed Data)     |
                                           +-------------------------------+

## Components

### Producer

- **Location:** `producer/` directory
- **Key Files:**
  - Dockerfile: [producer/Dockerfile](producer/Dockerfile)
  - Python script: `producer.py`
  - Dependencies: Defined in `producer/requirements.txt`

### Consumer

- **Location:** `consumer/` directory
- **Key Files:**
  - Dockerfile: [consumer/Dockerfile](consumer/Dockerfile)
  - Python script: `consumer.py`
  - Dependencies: Defined in `consumer/requirements.txt`

### Spark Processor

- **Location:** `spark-processor/` directory
- **Key Files:**
  - Dockerfile: [spark-processor/Dockerfile](spark-processor/Dockerfile)
  - Python script: `spark_processor.py`

## Infrastructure

The infrastructure is defined using Terraform in the `terraform/` directory. Key files include:

- `main.tf`: Main Terraform configuration file.
- `variables.tf`: Declares the variables used within the configuration.
- `outputs.tf`: Contains outputs including the service account key, which is used for this project.

## Setup Instructions

### 1. Terraform Setup

- Navigate to the `terraform/` directory.
- Initialize Terraform:

    ```sh
    terraform init
    ```

- Apply the configuration:

    ```sh
    terraform apply
    ```

### 2. Service Account Key

After applying Terraform, extract the service account key using the output provided and save it to `secrets/service-account.json`:

```bash
terraform output -raw service_account_key | base64 --decode > secrets/service-account.json
```

### 3. Environment Variables

Create or update your `.env` file (use [`.env.example`](.env.example) as a reference) with the following values:

```
GCP_PROJECT_ID=your-gcp-project-id
BQ_DATASET_ID=your_dataset_id
BQ_RAW_TABLE_ID=raw_reviews
BQ_PROCESSED_TABLE_ID=reviews_for_ml
TEMP_GCS_BUCKET=your-temp-gcs-bucket
KAFKA_BOOTSTRAP_SERVERS=your_kafka_bootstrap_servers
KAFKA_TOPIC=your_kafka_topic
KAFKA_GROUP_ID=your_kafka_group_id
```

### 4. Running the Components

Each component is containerized. Use Docker Compose (with the provided [docker-compose.yml](docker-compose.yml)) to run the entire stack or build/run individual containers as needed:

```sh
docker-compose up --build
```

## Additional Files

- **Docker Compose:** [docker-compose.yml](docker-compose.yml) orchestrates the multi-container setup.
- **Secrets:** Place all sensitive credentials and keys in the `secrets/` directory.
- **Git Ignore:** Refer to [.gitignore](.gitignore) for files and directories that are excluded from version control.

## Notes

- Ensure that you have Docker, Terraform, and the necessary dependencies for Python installed.
- Review the individual requirements.txt files in each component directory for required Python packages.

Happy coding!