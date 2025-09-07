import logging  

from app.topics import topic_banned_words
from app.tables import table_banned_words

from app.app import message_app

logger = logging.getLogger(__name__)

# Агент для обработки запрещенных слов
@message_app.agent(topic_banned_words)
async def process_banned_words(stream):
    async for item in stream:
        logger.info(item)

        if item.action == "add":
            if item.word not in table_banned_words:
                table_banned_words[item.word] = True
                logger.info(f"Слово '{item.word}' добавлено в список запрещенных слов")
            else:
                logger.info(f"Слово '{item.word}' уже есть в списке запрещенных слов")

        elif item.action == "remove":
            if item.word in table_banned_words:
                del table_banned_words[item.word]
                logger.info(f"Слово '{item.word}' удалено из списка запрещенных слов")
            else:
                logger.info(f"Слово '{item.word}' не было в списке запрещенных слов")
