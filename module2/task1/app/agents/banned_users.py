import logging  

from app.topics import topic_banned_users
from app.tables import table_banned_users

from app.app import message_app

logger = logging.getLogger(__name__)

# Агент для обработки забаненных пользователей
@message_app.agent(topic_banned_users)
async def process_banned_users(stream):
    async for item in stream:
        logger.info(item)

        if item.action == "add":
            if item.banned_user_id not in table_banned_users[item.user_id]:
                table_banned_users[item.user_id] = table_banned_users[item.user_id] + [item.banned_user_id]
                logger.info(f"Пользователь {item.user_id} забанил пользователя {item.banned_user_id}")
            else:
                logger.info(f"Пользователь {item.user_id} уже ранее забанил пользователя {item.banned_user_id}")

        elif item.action == "remove":
            if item.banned_user_id in table_banned_users[item.user_id]:
                table_banned_users[item.user_id] = [user for user in table_banned_users[item.user_id] if user != item.banned_user_id]
                logger.info(f"Пользователь {item.user_id} разбанил пользователя {item.banned_user_id}")
            else:
                logger.info(f"Пользователь {item.user_id} не банил пользователя {item.banned_user_id}")
