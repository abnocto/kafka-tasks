### Запуск инфраструктуры
```bash
docker compose up -d
```

### Создание топиков
```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-topics.sh --bootstrap-server kafka-0:9092 --create --topic messages --partitions 3 --replication-factor 2

docker exec -it $(docker compose ps -q kafka-0) kafka-topics.sh --bootstrap-server kafka-0:9092 --create --topic user_statistics --partitions 3 --replication-factor 2
```

### Проверка статуса
```bash
docker compose ps
```

### Отправка сообщений для проверки в топик `messages`
```bash
echo 'Bob:{"user_id": "Bob", "recipient_id": "Alice", "message": "Привет!", "timestamp": 1757239224902}' | docker exec -i $(docker compose ps -q kafka-0) kafka-console-producer.sh --bootstrap-server kafka-0:9092 --topic messages --property "parse.key=true" --property "key.separator=:"

echo 'Bob:{"user_id": "Bob", "recipient_id": "Alice", "message": "Привет еще раз!", "timestamp": 1757239247670}' | docker exec -i $(docker compose ps -q kafka-0) kafka-console-producer.sh --bootstrap-server kafka-0:9092 --topic messages --property "parse.key=true" --property "key.separator=:"

echo 'Bob:{"user_id": "Bob", "recipient_id": "Alice", "message": "Привет снова!", "timestamp": 1757239252050}' | docker exec -i $(docker compose ps -q kafka-0) kafka-console-producer.sh --bootstrap-server kafka-0:9092 --topic messages --property "parse.key=true" --property "key.separator=:"

echo 'Alice:{"user_id": "Alice", "recipient_id": "Bob", "message": "И тебе привет!", "timestamp": 1757239255353}' | docker exec -i $(docker compose ps -q kafka-0) kafka-console-producer.sh --bootstrap-server kafka-0:9092 --topic messages --property "parse.key=true" --property "key.separator=:"

echo 'Alice:{"user_id": "Alice", "recipient_id": "Bob", "message": "Как дела?", "timestamp": 1757239258499}' | docker exec -i $(docker compose ps -q kafka-0) kafka-console-producer.sh --bootstrap-server kafka-0:9092 --topic messages --property "parse.key=true" --property "key.separator=:"

echo 'Bob:{"user_id": "Bob", "recipient_id": "Random", "message": "Тебе тоже привет!", "timestamp": 1757239259342}' | docker exec -i $(docker compose ps -q kafka-0) kafka-console-producer.sh --bootstrap-server kafka-0:9092 --topic messages --property "parse.key=true" --property "key.separator=:"
```

### Запросы к KsqlDB для проверки
```sql
-- общее число сообщений
SELECT * FROM MESSAGES_COUNT_TABLE;

-- общее число уникальных получателей сообщений
SELECT * FROM UNIQUE_RECIPIENTS_COUNT_TABLE;

-- статистика по пользователям (число сообщений, число уникальных получателей сообщений)
SELECT * FROM USER_STATISTICS_TABLE;
```

Дополнительно статистика по пользователям пишется в топик `user_statistics`.
