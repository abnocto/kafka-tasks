## Запуск и проверка решения

### 1. Запуск и проверка инфраструктуры

````bash
docker compose up -d

```bash
docker compose ps
````

### 2. Подготовка БД и таблиц

- Подключение к postgres (БД `module4`)

```bash
docker exec -it postgres psql -h 127.0.0.1 -U postgres-user -d module4
```

- Создание таблицы `users`

```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100),
  email VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

- Создание таблицы `orders`

```sql
CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id),
  product_name VARCHAR(100),
  quantity INT,
  order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. Настройка Debezium Connector

- Проверка информации о кластере Kafka Connect

```bash
curl -s localhost:8083 | jq
```

- Проверка установленных плагинов

```bash
curl localhost:8083/connector-plugins | jq
```

- Конфигурация коннектора `module4-connector` для отслеживания изменений в БД `module4` для таблиц `users` и `orders`

```bash
curl -X PUT -H 'Content-Type: application/json' --data @kafka-connect/connector.json http://localhost:8083/connectors/module4-connector/config | jq
```

- Проверка статуса коннектора `module4-connector`

```bash
curl http://localhost:8083/connectors/module4-connector/status | jq
```

### 4. Добавление тестовых данных в БД для проверки решения

- Подключение к postgres (БД `module4`)

```bash
docker exec -it postgres psql -h 127.0.0.1 -U postgres-user -d module4
```

- Добавление данных

```sql
-- Добавление пользователей
INSERT INTO users (name, email) VALUES ('John Doe', 'john@example.com');
INSERT INTO users (name, email) VALUES ('Jane Smith', 'jane@example.com');
INSERT INTO users (name, email) VALUES ('Alice Johnson', 'alice@example.com');
INSERT INTO users (name, email) VALUES ('Bob Brown', 'bob@example.com');


-- Добавление заказов
INSERT INTO orders (user_id, product_name, quantity) VALUES (1, 'Product A', 2);
INSERT INTO orders (user_id, product_name, quantity) VALUES (1, 'Product B', 1);
INSERT INTO orders (user_id, product_name, quantity) VALUES (2, 'Product C', 5);
INSERT INTO orders (user_id, product_name, quantity) VALUES (3, 'Product D', 3);
INSERT INTO orders (user_id, product_name, quantity) VALUES (4, 'Product E', 4);
```

### 5. Получение данных из топиков Kafka

#### Самописный консьюмер
```bash
python3 consumer.py
```

#### kafka-console-consumer

- Просмотр доступных топиков

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --list
```

- Чтение данных из топика `module4.public.users` (создан для данных из таблицы `users`)

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-console-consumer.sh \
  --bootstrap-server kafka-0:9092 \
  --topic module4.public.users \
  --from-beginning
```

- Чтение данных из топика `module4.public.orders` (создан для данных из таблицы `orders`)

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-console-consumer.sh \
  --bootstrap-server kafka-0:9092 \
  --topic module4.public.orders \
  --from-beginning
```

## Назначение компонентов и взаимосвязи

### Компоненты и связь между ними

#### Kafka кластер (порты 9094, 9095, 9096)

- Три брокера kafka-0, kafka-1, kafka-2
- Работает в KRaft режиме

#### Kafka UI (порт 8080)

- Веб-интерфейс для управления и мониторинга Kafka кластера
- Зависит от Kafka кластера

#### Schema Registry (порт 8081)

- Управляет схемами данных для Kafka
- Зависит от Kafka кластера

#### PostgreSQL (порт 5432)

- Реляционная база данных
- Создана БД `module4` с таблицами `users` и `orders`

#### Kafka Connect (порты 8083, 9875, 9876)

- Платформа для интеграции Kafka с внешними системами
- Настроен Debezium коннектор для CDC (захвата изменения данных в БД)
- Данные из БД записываются в Kafka топики: `module4.public.users`, `module4.public.orders`
- Дополнительно настроен экспорт JMX метрик, которые в дальнейшем собирает Prometheus
- Зависит от Kafka кластера, Schema Registry, PostgreSQL
- **Порт 8083**: REST API для управления коннекторами
- **Порт 9875**: Порт для экспорта JMX метрик
- **Порт 9876**: Порт для сбора метрик с помощью Prometheus

#### Prometheus (порт 9090)

- Система мониторинга и сбора метрик
- Настроен сбор JMX метрик от Kafka Connect (порт 9876)
- Зависит от Kafka Connect

#### Grafana (порт 3001)

- Система визуализации метрик и дашбордов
- Настроены дашборды для визуализации данных из датасорса Prometheus (порт 9090)
- Зависит от Prometheus

### Потоки данных

```
PostgreSQL
  -> (CDC через Debezium)
Kafka Connect
  -> (публикация в топики)
Kafka

Kafka Connect
  -> (метрики)
Prometheus
  -> (дашборды)
Grafana
```

### Доступные веб интерфейсы

- **Kafka UI** (http://localhost:8080)
- **Kafka Connect** (http://localhost:8083)
- **Prometheus** (http://localhost:9090)
- **Grafana** (http://localhost:3001)

## Описание конфигурации Debezium коннектора

### Основные параметры подключения к БД:

- `connector.class: "io.debezium.connector.postgresql.PostgresConnector"` - класс коннектора
- `database.hostname: "postgres"` - хост БД
- `database.port: "5432"` - порт БД
- `database.user: "postgres-user"` - пользователь БД
- `database.password: "postgres-pw"` - пароль БД
- `database.dbname: "module4"` - название БД
- `database.server.name: "module4"` - имя сервера БД

### Настройки отслеживания таблиц:

- `table.include.list: "public.users,public.orders"` - список таблиц для отслеживания изменений

### Трансформации данных:

- `transforms: "unwrap"` - название трансформации
- `transforms.unwrap.type: "io.debezium.transforms.ExtractNewRecordState"` - используем только структуру данных о новом состоянии записи вместо расширенной
- `transforms.unwrap.drop.tombstones: "false"` - сохраняем сообщения, указывающие на удаление записей
- `transforms.unwrap.delete.handling.mode: "rewrite"` - режим обработки операций удаления (переписываем сообщения об удалении)

### Настройки топиков:

- `topic.prefix: "module4"` - префикс для имени топиков
- `topic.creation.enable: "true"` - автоматическое создание топиков включено
- `topic.creation.default.replication.factor: "1"` - фактор репликации для новых топиков
- `topic.creation.default.partitions: "1"` - количество партиций для новых топиков

### Дополнительные параметры:

- `skipped.operations: "none"` - не пропускать никакие операции (INSERT, UPDATE, DELETE)
