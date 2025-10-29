FROM confluentinc/cp-kafka-connect:7.7.1

RUN confluent-hub install --no-prompt confluentinc/kafka-connect-json-schema-converter:latest && \
    confluent-hub install --no-prompt confluentinc/kafka-connect-elasticsearch:latest