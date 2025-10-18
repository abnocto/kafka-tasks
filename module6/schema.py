from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONSerializer, JSONDeserializer

class AnalyticsEvent:
    @staticmethod
    def from_dict(dict: dict) -> 'AnalyticsEvent':
        return AnalyticsEvent(id=dict['id'], type=dict['type'], timestamp=dict['timestamp'], serialized_data=dict['serialized_data'])

    def __init__(self, id: str, type: str, timestamp: str, serialized_data: str):
        self.id = id
        self.type = type
        self.timestamp = timestamp
        self.serialized_data = serialized_data

    def __str__(self) -> str:
        return f"AnalyticsEvent(id={self.id}, type={self.type}, timestamp={self.timestamp}, serialized_data={self.serialized_data})"

    def to_dict(self) -> dict:
        return {'id': self.id, 'type': self.type, 'timestamp': self.timestamp, 'serialized_data': self.serialized_data}

def analytics_event_to_dict(analytics_event: AnalyticsEvent, ctx) -> dict:
    return analytics_event.to_dict()

def analytics_event_from_dict(dict: dict, ctx) -> AnalyticsEvent:
    return AnalyticsEvent.from_dict(dict)

schema_registry_client = SchemaRegistryClient({
    "url": "http://localhost:8081",
})

analytics_event_schema = """
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "AnalyticsEvent",
    "type": "object",
    "properties": {
    "id": {
        "type": "string"
    },
    "type": {
        "type": "string"
    },
    "timestamp": {
        "type": "string"
    },
    "serialized_data": {
        "type": "string"
    }
 },
 "required": ["id", "type", "timestamp", "serialized_data"]
}
"""

analytics_event_serializer = JSONSerializer(analytics_event_schema, schema_registry_client, analytics_event_to_dict)
analytics_event_deserializer = JSONDeserializer(analytics_event_schema, analytics_event_from_dict, schema_registry_client)
