### Запуск инфраструктуры

```bash
docker compose up -d
```

### Проверка статуса

```bash
docker compose ps
```

### Kafka UI

http://localhost:8080

### Grafana

http://localhost:3001

### Prometheus

http://localhost:9090

### Перформанс тест (запись)

```bash
docker exec -it kafka-0 \
  kafka-producer-perf-test.sh \
  --throughput 500 \
  --num-records 100000000 \
  --topic demo-topic \
  --record-size 100 \
  --producer-props bootstrap.servers=kafka-0:9092
```

### Перформанс тест (чтение)

```bash
docker exec -it kafka-0 \
  kafka-consumer-perf-test.sh \
  --messages 100000000 \
  --timeout 1000000 \
  --topic demo-topic \
  --reporting-interval 1000 \
  --show-detailed-stats \
  --bootstrap-server kafka-0:9092
```
