from app.app import items_validator_app
from app.schema import items_banned_topic_name

table_items_banned = items_validator_app.Table(
    items_banned_topic_name,
    default=bool,
    partitions=3,
)
