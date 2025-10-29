from faust import Codec

from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONDeserializer, JSONSerializer
from confluent_kafka.serialization import SerializationContext, MessageField

class SchemaRegistryCodec(Codec):
    def __init__(self, schema_registry_client, schema_str, topic_name):
        super().__init__()
        
        self.serializer = JSONSerializer(
            schema_str,
            schema_registry_client,
            lambda data, ctx: data,
            conf={"auto.register.schemas": False}
        )

        self.deserializer = JSONDeserializer(
            schema_str,
            lambda data, ctx: data
        )

        self.topic_name = topic_name
    
    def _loads(self, bytes):
        return self.deserializer(bytes, SerializationContext(self.topic_name, MessageField.VALUE))
    
    def _dumps(self, obj):
        return self.serializer(obj, SerializationContext(self.topic_name, MessageField.VALUE))

schema_registry_client = SchemaRegistryClient({
    "url": "http://schema-registry:8081",
})

items_raw_topic_name = "items-raw"
items_raw_schema = schema_registry_client.get_latest_version("items-raw-value")
items_raw_codec = SchemaRegistryCodec(schema_registry_client, items_raw_schema.schema.schema_str, items_raw_topic_name)

items_banned_topic_name = "items-banned"
items_banned_schema = schema_registry_client.get_latest_version("items-banned-value")
items_banned_codec = SchemaRegistryCodec(schema_registry_client, items_banned_schema.schema.schema_str, items_banned_topic_name)

items_validated_topic_name = "items-validated"
items_validated_schema = schema_registry_client.get_latest_version("items-validated-value")
items_validated_codec = SchemaRegistryCodec(schema_registry_client, items_validated_schema.schema.schema_str, items_validated_topic_name)
