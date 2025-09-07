import logging

from app.entities.message import Message

from app.topics import topic_messages, topic_filtered_messages
from app.tables import table_banned_users, table_banned_words

from app.app import message_app

logger = logging.getLogger(__name__)

# Канал для обработки сообщений (для разделения логики фильтрации и санитайзинга/отправки)
messages_channel = message_app.channel(value_type=Message)

# Функция для санитайзинга сообщения
def sanitize_message(message: Message, banned_words: list) -> Message:
    text = message.text

    for word in banned_words:
        mask = "*" * len(word)
        text = text.replace(word, mask)
    
    return Message(sender_id=message.sender_id, recipient_id=message.recipient_id, text=text)

# Агент для обработки сообщений - выполняет фильтрацию по забаненным пользователям
@message_app.agent(topic_messages)
async def filter_messages(stream):
    async for item in stream:
        logger.info(item)

        is_sender_banned = item.sender_id in table_banned_users[item.recipient_id]

        if is_sender_banned:
            logger.info(f"Отправка заблокирована: пользователь {item.recipient_id} забанил пользователя {item.sender_id}")
            continue

        await messages_channel.send(value=item)

# Агент для обработки сообщений - выполняет санитайзинг сообщений и отправку в filtered-messages
@message_app.agent(messages_channel)
async def sanitize_and_send_messages(stream):
    async for item in stream:
        banned_words = list(table_banned_words.keys())
        sanitized_item = sanitize_message(item, banned_words)

        await topic_filtered_messages.send(
            key=sanitized_item.recipient_id,
            value=sanitized_item,
        )

        logger.info(f"Сообщение отправлено от пользователя {sanitized_item.sender_id} пользователю {sanitized_item.recipient_id}: {sanitized_item.text}")
