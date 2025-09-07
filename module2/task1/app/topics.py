from app.entities.message import Message
from app.entities.banned_user import BannedUser
from app.entities.banned_word import BannedWord

from app.app import message_app

# Топик отправляемых сообщений
topic_messages = message_app.topic(
    "messages", 
    key_type=str, 
    value_type=Message,
)

# Топик отфильтрованных сообщений
topic_filtered_messages = message_app.topic(
    "filtered-messages", 
    key_type=str, 
    value_type=Message,
)

# Топик забанненых пользователей
topic_banned_users = message_app.topic(
    "banned-users", 
    key_type=str, 
    value_type=BannedUser,
)

# Топик запрещенных слов
topic_banned_words = message_app.topic(
    "banned-words", 
    key_type=str, 
    value_type=BannedWord,
)
