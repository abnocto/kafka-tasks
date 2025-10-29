from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONSerializer

schema_registry_client = SchemaRegistryClient({
    "url": "http://schema-registry:8081",
})

client_search_request_schema = schema_registry_client.get_latest_version("client-search-requests-value")

client_search_request_serializer = JSONSerializer(
    client_search_request_schema.schema.schema_str,
    schema_registry_client,
    lambda value, ctx: value,
    conf={"auto.register.schemas": False}
)

