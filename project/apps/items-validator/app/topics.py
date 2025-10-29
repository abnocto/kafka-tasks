from app.app import items_validator_app
from app.schema import items_raw_topic_name, items_banned_topic_name, items_validated_topic_name, items_raw_codec, items_banned_codec, items_validated_codec

items_raw_topic = items_validator_app.topic(
    items_raw_topic_name,
    key_type=str,
    value_serializer=items_raw_codec,
)

items_banned_topic = items_validator_app.topic(
    items_banned_topic_name,
    key_type=str,
    value_serializer=items_banned_codec,
)

items_validated_topic = items_validator_app.topic(
    items_validated_topic_name,
    key_type=str,
    value_serializer=items_validated_codec,
)
