import logging

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, struct
from pyspark.sql.types import StructType, StructField, StringType, BinaryType

from app.schema import decode_client_search_request, encode_client_recommendation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

kafka_servers = "kafka-secondary-0:9092,kafka-secondary-1:9092,kafka-secondary-2:9092"
jaas_config = 'org.apache.kafka.common.security.plain.PlainLoginModule required username="analytics" password="analytics-secret";'

client_search_request_schema = StructType([
    StructField("user_id", StringType(), True),
    StructField("query", StringType(), True),
    StructField("result", StringType(), True)
])

decode_udf = udf(decode_client_search_request, client_search_request_schema)
encode_udf = udf(lambda row: encode_client_recommendation(row.asDict()), BinaryType())

def write_to_kafka(batch_df, batch_id):
    logger.info(f"Обработан батч {batch_id}, записей: {batch_df.count()}")
    
    batch_df.write \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_servers) \
        .option("topic", "client-recommendations") \
        .option("kafka.security.protocol", "SASL_SSL") \
        .option("kafka.ssl.truststore.location", "/ssl/ca.truststore.jks") \
        .option("kafka.ssl.truststore.password", "kafka-password") \
        .option("kafka.sasl.mechanism", "PLAIN") \
        .option("kafka.sasl.jaas.config", jaas_config) \
        .save()

def run():
    spark = SparkSession.builder \
        .appName("Analytics") \
        .master("local[*]") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
        .config("spark.hadoop.fs.defaultFS", "hdfs://hadoop-namenode:9000") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("INFO")
    
    input_data_frame = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_servers) \
        .option("subscribe", "client-search-requests") \
        .option("startingOffsets", "earliest") \
        .option("kafka.security.protocol", "SASL_SSL") \
        .option("kafka.ssl.truststore.location", "/ssl/ca.truststore.jks") \
        .option("kafka.ssl.truststore.password", "kafka-password") \
        .option("kafka.sasl.mechanism", "PLAIN") \
        .option("kafka.sasl.jaas.config", jaas_config) \
        .load()
    
    # Просто сохраняем как рекомендацию последние найденные для пользователя результаты поиска
    # Не записываем рекомендацию, если результат поиска пустой
    processed_data_frame = input_data_frame \
        .withColumn("client_search_request", decode_udf(col("value"))) \
        .select("client_search_request.*") \
        .filter(col("result") != "[]") \
        .select(
            col("user_id").alias("key"),
            encode_udf((struct(col("user_id"), col("result").alias("recommendations")))).alias("value")
        )
    
    query = processed_data_frame.writeStream \
        .foreachBatch(write_to_kafka) \
        .option("checkpointLocation", "hdfs://hadoop-namenode:9000/spark/checkpoints/analytics") \
        .start()
    
    query.awaitTermination()

if __name__ == "__main__":
    run()
