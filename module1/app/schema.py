import os

from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONSerializer, JSONDeserializer

from app.item import Item

schema_registry_client = SchemaRegistryClient({
    "url": os.getenv('SCHEMA_REGISTRY_URL')
})

items_schema = """
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Item",
    "type": "object",
    "properties": {
    "id": {
        "type": "string"
    },
    "name": {
        "type": "string"
    },
    "price": {
        "type": "integer"
    }
 },
 "required": ["id", "name", "price"]
}
"""

def item_to_dict(item: Item, ctx) -> dict:
    return item.to_dict()

def item_from_dict(dict: dict, ctx) -> Item:
    return Item.from_dict(dict)

items_serializer = JSONSerializer(items_schema, schema_registry_client, item_to_dict)
items_deserializer = JSONDeserializer(items_schema, item_from_dict, schema_registry_client)
