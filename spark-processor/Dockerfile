FROM bitnami/spark:latest

USER root

RUN apt-get update && apt-get install -y curl

RUN mkdir -p /root/.ivy2/jars
WORKDIR /root/.ivy2/jars

RUN curl -O https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar
RUN curl -L -O https://repo1.maven.org/maven2/com/google/cloud/spark/spark-bigquery-with-dependencies_2.12/0.25.2/spark-bigquery-with-dependencies_2.12-0.25.2.jar
RUN curl -L -O https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.3.0/spark-sql-kafka-0-10_2.12-3.3.0.jar
RUN curl -L -O https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.3.0/spark-token-provider-kafka-0-10_2.12-3.3.0.jar
RUN curl -L -O https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/2.8.1/kafka-clients-2.8.1.jar

RUN pip install --no-cache-dir \
    pyspark==3.3.0 \
    kafka-python \
    google-cloud-bigquery \
    google-cloud-storage

WORKDIR /app
RUN mkdir -p /tmp/checkpoints && chmod 777 /tmp/checkpoints

ENV PYTHONPATH=/app

COPY spark_processor.py /app/

CMD ["python", "spark_processor.py"]