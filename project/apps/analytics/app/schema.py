import logging

from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONDeserializer, JSONSerializer
from confluent_kafka.serialization import SerializationContext, MessageField

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

schema_registry_client = SchemaRegistryClient({
    "url": "http://schema-registry:8081"
})

client_search_request_schema = schema_registry_client.get_latest_version("client-search-requests-value")

client_search_request_deserializer = JSONDeserializer(
    client_search_request_schema.schema.schema_str,
    lambda data, ctx: data,
)

client_recommendation_schema = schema_registry_client.get_latest_version("client-recommendations-value")

client_recommendation_serializer = JSONSerializer(
    client_recommendation_schema.schema.schema_str,
    schema_registry_client,
    lambda value, ctx: value,
    conf={"auto.register.schemas": False}
)

def decode_client_search_request(bytes):
    return client_search_request_deserializer(
        bytes,
        SerializationContext("client-search-requests", MessageField.VALUE)
    )

def encode_client_recommendation(obj):
    return client_recommendation_serializer(
        obj,
        SerializationContext("client-recommendations", MessageField.VALUE)
    )
