import logging

from app.app import items_validator_app
from app.topics import items_raw_topic, items_validated_topic
from app.tables import table_items_banned

logger = logging.getLogger(__name__)

@items_validator_app.agent(items_raw_topic)
async def process_items(stream):
    async for item in stream:
        item_name = item.get('name', '')
        
        if item_name in table_items_banned:
            logger.info(f"Товар '{item_name}' заблокирован, пропускаем")
            continue
        
        await items_validated_topic.send(
            key=item_name,
            value=item,
        )
        
        logger.info(f"Товар '{item_name}' проверен и записан в items-validated")
