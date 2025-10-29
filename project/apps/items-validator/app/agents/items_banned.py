import logging  

from app.app import items_validator_app
from app.topics import items_banned_topic
from app.tables import table_items_banned

logger = logging.getLogger(__name__)

@items_validator_app.agent(items_banned_topic)
async def process_items_banned(stream):
    async for item_name, banned_info in stream.items():
        if banned_info is None:
            if item_name in table_items_banned:
                del table_items_banned[item_name]
                logger.info(f"Товар '{item_name}' удалён из списка заблокированных товаров")
            else:
                logger.info(f"Товар '{item_name}' не был в списке заблокированных товаров")
        
        else:
            if item_name not in table_items_banned:
                table_items_banned[item_name] = True
                logger.info(f"Товар '{item_name}' добавлен в список заблокированных товаров")
            else:
                logger.info(f"Товар '{item_name}' уже был в списке заблокированных товаров")
