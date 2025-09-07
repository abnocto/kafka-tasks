from app.app import message_app

# Таблица забаненных пользователей (каждый воркер имеет доступ только к данным из "своей" партиции)
table_banned_users = message_app.Table(
    "banned-users",  
    default=list,
    # Важно, чтобы число партиций было равно числу партиций топика banned-users
    partitions=3,
)

# Глобальная таблица запрещенных слов (каждый воркер имеет доступ ко всем данным)
table_banned_words = message_app.GlobalTable(
    "banned-words",
    default=bool,
    partitions=1,
)
