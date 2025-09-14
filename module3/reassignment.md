Cоздадим топик mytopic с 3 партициями и фактором репликации 2, если еще не был создан:

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-topics.sh --bootstrap-server localhost:9092 --create --topic mytopic --partitions 3 --replication-factor 2 --if-not-exists
```

Выведем все топики в кластере:

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-topics.sh --bootstrap-server localhost:9092 --list
```

Выведем информацию о топике mytopic:

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic mytopic
```

Увеличим число партиций топика mytopic до 8:

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-topics.sh --bootstrap-server localhost:9092 --alter --topic mytopic --partitions 8
```

Удалим топик mytopic:

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-topics.sh --bootstrap-server localhost:9092 --delete --topic mytopic
```

Cоздадим заново топик mytopic с 8 партициями и фактором репликации 2, если еще не был создан:

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-topics.sh --bootstrap-server localhost:9092 --create --topic mytopic --partitions 8 --replication-factor 2 --if-not-exists
```

Выведем информацию о топиках, у которых есть партиции с недостаточным числом реплик:

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-topics.sh --bootstrap-server localhost:9092 --describe --under-replicated-partitions
```

Выведем информацию о топиках, у которых есть партиции, синхронизация которых меньше min.insync.replicas:

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-topics.sh --bootstrap-server localhost:9092 --describe --under-min-isr-partitions
```

Выведем информацию о топиках, у которых есть партиции без доступного лидера:

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-topics.sh --bootstrap-server localhost:9092 --describe --unavailable-partitions
```

Можно проверить, имитировав сбой, например, остановив один из брокеров:

```bash
docker compose stop kafka-2
```

Запустим брокер заново:

```bash
docker compose start kafka-2
```

После этого нарушился баланс по лидерам партиций. Запустим перевыборы:

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-leader-election.sh --bootstrap-server localhost:9092 --election-type PREFERRED --all-topic-partitions
```

Добавим новый брокер kafka-3:

- Добавим новый брокер в docker-compose.
- Перезапустим кластер.

После этого переназначим партиции между брокерами:

- Подключимся к контейнеру:

```bash
docker exec -it $(docker compose ps -q kafka-0) /bin/bash
```

- Сохраним JSON файл с планом переназначения партиций:

```bash
cd /tmp

echo '{
  "version": 1,
  "partitions": [
    {"topic": "mytopic", "partition": 0, "replicas": [0, 1], "log_dirs": ["any", "any"]},
    {"topic": "mytopic", "partition": 1, "replicas": [1, 2], "log_dirs": ["any", "any"]},
    {"topic": "mytopic", "partition": 2, "replicas": [2, 3], "log_dirs": ["any", "any"]},
    {"topic": "mytopic", "partition": 3, "replicas": [3, 0], "log_dirs": ["any", "any"]},
    {"topic": "mytopic", "partition": 4, "replicas": [0, 2], "log_dirs": ["any", "any"]},
    {"topic": "mytopic", "partition": 5, "replicas": [1, 3], "log_dirs": ["any", "any"]},
    {"topic": "mytopic", "partition": 6, "replicas": [2, 0], "log_dirs": ["any", "any"]},
    {"topic": "mytopic", "partition": 7, "replicas": [3, 1], "log_dirs": ["any", "any"]}
  ]
}' > reassignment.json
```

- Сгенерируем план:

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-reassign-partitions.sh --bootstrap-server localhost:9092 --broker-list "1,2,3,4" --topics-to-move-json-file "/tmp/reassignment.json" --generate
```

- Выполним переназначение:

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-reassign-partitions.sh --bootstrap-server localhost:9092 --reassignment-json-file /tmp/reassignment.json --execute
```

- Выполним верификацию (проверим статус) переназначения:

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-reassign-partitions.sh --bootstrap-server localhost:9092 --reassignment-json-file /tmp/reassignment.json --verify
```

- Проверим, есть ли активные консюмер группы:

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list
```

Запустим консольного консюмера для топика mytopic в группу consumer:

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic mytopic --group consumer
```

- Вариант с дополнительными опциями и форматированием:

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic mytopic \
  --group consumer \
  --from-beginning \
  --max-messages 10 \
  --formatter kafka.tools.DefaultMessageFormatter \
  --property print.key=true \
  --property print.value=true \
  --property key.separator=" => "
```

Запустим консольного продюсера для топика mytopic:

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-console-producer.sh \
    --bootstrap-server localhost:9092 \
    --topic mytopic \
    --property parse.key=true \
    --property key.separator=" => "
```

Сбросим смещение для группы:

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --topic mytopic \
  --group consumer \
  --reset-offsets \
  --to-earliest \
  --execute
```

Удалим консюмер группу:

- Проверим, нет ли активных членов группы:

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group consumer
```

- Удалим группу:

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-consumer-groups.sh --bootstrap-server localhost:9092 --delete --group consumer
```
