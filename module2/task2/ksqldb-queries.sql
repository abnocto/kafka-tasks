-- Создание стрима messages_stream для чтения сообщений из топика messages
CREATE STREAM messages_stream (
    user_id STRING,
    recipient_id STRING,
    message STRING,
    timestamp BIGINT
)
WITH (
    KAFKA_TOPIC='messages',
    VALUE_FORMAT='json',
    PARTITIONS=3
);

-- Создание таблицы messages_count_table для подсчета общего количества сообщений
CREATE TABLE messages_count_table AS
SELECT 'global_key' as global_key, COUNT(*) as messages_count
FROM messages_stream
GROUP BY 'global_key'
EMIT CHANGES;

-- Создание таблицы unique_recipients_count_table для подсчета общего количества уникальных получателей сообщений
CREATE TABLE unique_recipients_count_table AS
SELECT 'global_key' as global_key, COUNT_DISTINCT(recipient_id) as unique_recipients_count
FROM messages_stream
GROUP BY 'global_key'
EMIT CHANGES;

-- Создание таблицы user_statistics_table для подсчета агрегированных данных по пользователям
CREATE TABLE user_statistics_table AS
SELECT user_id, COUNT(*) as user_messages_count, COUNT_DISTINCT(recipient_id) as user_unique_recipients_count
FROM messages_stream
GROUP BY user_id
EMIT CHANGES;

-- Создание стрима user_statistics_table_stream для чтения агрегированных данных по пользователям из топика таблицы user_statistics_table
CREATE STREAM user_statistics_table_stream (
    user_id STRING KEY,
    user_messages_count BIGINT,
    user_unique_recipients_count BIGINT
)
WITH (
    KAFKA_TOPIC='USER_STATISTICS_TABLE',
    VALUE_FORMAT='json',
    PARTITIONS=3
);

-- Создание стрима user_statistics_stream для записи агрегированных данных по пользователям из стрима user_statistics_table_stream в топик user_statistics
CREATE STREAM user_statistics_stream
WITH (
    KAFKA_TOPIC='user_statistics',
    VALUE_FORMAT='json',
    PARTITIONS=3
) AS 
SELECT 
    user_id,
    user_messages_count,
    user_unique_recipients_count
FROM user_statistics_table_stream
EMIT CHANGES;