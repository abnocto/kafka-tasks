#!/bin/bash

set -e

sleep 5

echo "Creating client.properties"
cat > /tmp/client.properties <<EOF
security.protocol=SASL_SSL
ssl.truststore.location=/bitnami/kafka/config/certs/kafka.truststore.jks
ssl.truststore.password=kafka-password
sasl.mechanism=PLAIN
sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required username="admin" password="admin-secret";
EOF

BOOTSTRAP_SERVER_PRIMARY="kafka-primary-0:9092"
BOOTSTRAP_SERVER_SECONDARY="kafka-secondary-0:9092"

SCHEMA_REGISTRY_URL="http://schema-registry:8081"

ITEM_SCHEMA=$(cat /schemas/item.json | jq -c '.')
ITEM_BANNED_SCHEMA=$(cat /schemas/item-banned.json | jq -c '.')
CLIENT_SEARCH_REQUEST_SCHEMA=$(cat /schemas/client-search-request.json | jq -c '.')
CLIENT_RECOMMENDATION_SCHEMA=$(cat /schemas/client-recommendation.json | jq -c '.')

KSQLDB_URL="http://ksqldb-server:8088"

########################################################
# Kafka: Создаем топики

kafka-topics.sh --bootstrap-server "$BOOTSTRAP_SERVER_PRIMARY" \
  --command-config /tmp/client.properties \
  --create --if-not-exists \
  --topic items-raw \
  --partitions 3 \
  --replication-factor 3

kafka-topics.sh --bootstrap-server "$BOOTSTRAP_SERVER_PRIMARY" \
  --command-config /tmp/client.properties \
  --create --if-not-exists \
  --topic items-banned \
  --partitions 3 \
  --replication-factor 3 \
  --config cleanup.policy=compact \
  --config min.cleanable.dirty.ratio=0.01 \
  --config segment.ms=60000 \
  --config delete.retention.ms=60000 \
  --config min.compaction.lag.ms=0 \
  --config max.compaction.lag.ms=60000

kafka-topics.sh --bootstrap-server "$BOOTSTRAP_SERVER_PRIMARY" \
  --command-config /tmp/client.properties \
  --create --if-not-exists \
  --topic items-validator-app-items-banned-changelog \
  --partitions 3 \
  --replication-factor 3 \
  --config cleanup.policy=compact \
  --config min.cleanable.dirty.ratio=0.01 \
  --config segment.ms=60000 \
  --config delete.retention.ms=60000 \
  --config min.compaction.lag.ms=0 \
  --config max.compaction.lag.ms=60000

kafka-topics.sh --bootstrap-server "$BOOTSTRAP_SERVER_PRIMARY" \
  --command-config /tmp/client.properties \
  --create --if-not-exists \
  --topic items-validated \
  --partitions 3 \
  --replication-factor 3

kafka-topics.sh --bootstrap-server "$BOOTSTRAP_SERVER_PRIMARY" \
  --command-config /tmp/client.properties \
  --create --if-not-exists \
  --topic client-search-requests \
  --partitions 3 \
  --replication-factor 3

kafka-topics.sh --bootstrap-server "$BOOTSTRAP_SERVER_PRIMARY" \
  --command-config /tmp/client.properties \
  --create --if-not-exists \
  --topic client-recommendations \
  --partitions 3 \
  --replication-factor 3 \
  --config cleanup.policy=compact \
  --config min.cleanable.dirty.ratio=0.01 \
  --config segment.ms=60000 \
  --config delete.retention.ms=60000 \
  --config min.compaction.lag.ms=0 \
  --config max.compaction.lag.ms=60000

########################################################
# Kafka: Добавляем ACL (primary)

kafka-acls.sh --bootstrap-server "$BOOTSTRAP_SERVER_PRIMARY" \
  --command-config /tmp/client.properties \
  --add \
  --allow-principal User:shop-api \
  --operation Write \
  --topic items-raw

kafka-acls.sh --bootstrap-server "$BOOTSTRAP_SERVER_PRIMARY" \
  --command-config /tmp/client.properties \
  --add \
  --allow-principal User:client-api \
  --operation Write \
  --topic client-search-requests

kafka-acls.sh --bootstrap-server "$BOOTSTRAP_SERVER_PRIMARY" \
  --command-config /tmp/client.properties \
  --add \
  --allow-principal User:items-validator \
  --operation Read \
  --operation Describe \
  --topic items-raw

kafka-acls.sh --bootstrap-server "$BOOTSTRAP_SERVER_PRIMARY" \
  --command-config /tmp/client.properties \
  --add \
  --allow-principal User:items-validator \
  --operation Write \
  --operation Read \
  --operation Describe \
  --topic items-banned

kafka-acls.sh --bootstrap-server "$BOOTSTRAP_SERVER_PRIMARY" \
  --command-config /tmp/client.properties \
  --add \
  --allow-principal User:items-validator \
  --operation Write \
  --topic items-validated

kafka-acls.sh --bootstrap-server "$BOOTSTRAP_SERVER_PRIMARY" \
  --command-config /tmp/client.properties \
  --add \
  --allow-principal User:items-validator \
  --operation ALL \
  --resource-pattern-type prefixed \
  --topic items-validator-app-

kafka-acls.sh --bootstrap-server "$BOOTSTRAP_SERVER_PRIMARY" \
  --command-config /tmp/client.properties \
  --add \
  --allow-principal User:items-validator \
  --operation Read \
  --operation Describe \
  --group items-validator-app

########################################################
# Kafka: Добавляем ACL (secondary)

kafka-acls.sh --bootstrap-server "$BOOTSTRAP_SERVER_SECONDARY" \
  --command-config /tmp/client.properties \
  --add \
  --allow-principal User:analytics \
  --operation Read \
  --operation Describe \
  --topic client-search-requests

kafka-acls.sh --bootstrap-server "$BOOTSTRAP_SERVER_SECONDARY" \
  --command-config /tmp/client.properties \
  --add \
  --allow-principal User:analytics \
  --operation Write \
  --topic client-recommendations

kafka-acls.sh --bootstrap-server "$BOOTSTRAP_SERVER_SECONDARY" \
  --command-config /tmp/client.properties \
  --add \
  --allow-principal User:analytics \
  --operation Read \
  --operation Describe \
  --group analytics-group

########################################################
# Schema Registry: Регистрируем схемы

curl -X POST "$SCHEMA_REGISTRY_URL/subjects/items-raw-value/versions" \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d "{\"schemaType\": \"JSON\", \"schema\": $(echo "$ITEM_SCHEMA" | jq -Rs .)}"

curl -X POST "$SCHEMA_REGISTRY_URL/subjects/items-validated-value/versions" \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d "{\"schemaType\": \"JSON\", \"schema\": $(echo "$ITEM_SCHEMA" | jq -Rs .)}"

curl -X POST "$SCHEMA_REGISTRY_URL/subjects/items-banned-value/versions" \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d "{\"schemaType\": \"JSON\", \"schema\": $(echo "$ITEM_BANNED_SCHEMA" | jq -Rs .)}"

curl -X POST "$SCHEMA_REGISTRY_URL/subjects/client-search-requests-value/versions" \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d "{\"schemaType\": \"JSON\", \"schema\": $(echo "$CLIENT_SEARCH_REQUEST_SCHEMA" | jq -Rs .)}"

curl -X POST "$SCHEMA_REGISTRY_URL/subjects/client-recommendations-value/versions" \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d "{\"schemaType\": \"JSON\", \"schema\": $(echo "$CLIENT_RECOMMENDATION_SCHEMA" | jq -Rs .)}"

########################################################
# Добавляем коннектор (kafka-connect) для Elasticsearch

curl -X POST -H "Content-Type: application/json" --data @/kafka-connect-configs/elasticsearch-sink.json http://kafka-connect:8083/connectors

########################################################
# Kafka: Ожидаем репликации в secondary (MirrorMaker2)

for i in {1..24}; do
  TOPICS=$(kafka-topics.sh --bootstrap-server "$BOOTSTRAP_SERVER_SECONDARY" --command-config /tmp/client.properties --list)
  echo "$TOPICS" | grep -q "^client-recommendations$" && echo "$TOPICS" | grep -q "^client-search-requests$" && break
  [ $i -eq 24 ] && echo "Timeout!" && exit 1
  sleep 5
done

########################################################
# ksqlDB: Создаем стримы и таблицы

curl -X POST "$KSQLDB_URL/ksql" \
  -H "Content-Type: application/vnd.ksql.v1+json" \
  -d '{
    "ksql": "CREATE STREAM client_recommendations_stream WITH (KAFKA_TOPIC='\''client-recommendations'\'', VALUE_FORMAT='\''JSON_SR'\'');",
    "streamsProperties": {}
  }'

curl -X POST "$KSQLDB_URL/ksql" \
  -H "Content-Type: application/vnd.ksql.v1+json" \
  -d '{
    "ksql": "CREATE TABLE client_recommendations_table AS SELECT user_id, LATEST_BY_OFFSET(recommendations) AS recommendations FROM client_recommendations_stream GROUP BY user_id EMIT CHANGES;",
    "streamsProperties": {}
  }'
