## Запуск

```bash
docker-compose up -d
```

### Проверка работоспособности:

Приложения:

- Shop API (добавление товаров): http://localhost:8886
- Client API (поиск товаров и рекомендации): http://localhost:8887
- Items Validator (блокировка товаров): http://localhost:8888

Инфраструктура:

- Kafka UI: http://localhost:8080
- Kibana: http://localhost:5601
- Grafana: http://localhost:3001 (admin/kafka)
- Prometheus: http://localhost:9090

## Инструменты

| Компонент       | Назначение                                 |
| --------------- | ------------------------------------------ |
| Kafka (KRaft)   | Брокеры сообщений, 2 кластера по 3 брокера |
| Schema Registry | Управление схемами данных                  |
| MirrorMaker2    | Репликация между кластерами                |
| Kafka Connect   | Интеграция с внешними системами            |
| ksqlDB          | SQL-запросы к потокам данных               |
| Elasticsearch   | Полнотекстовый поиск товаров               |
| Kibana          | Визуализация данных из Elasticsearch       |
| HDFS            | Хранилище для Spark checkpoints            |
| Spark Streaming | Обработка потоков рекомендаций             |
| Prometheus      | Сбор метрик с брокеров                     |
| Grafana         | Визуализация метрик                        |
| Alertmanager    | Управление алертами                        |

## Реализация

### Kafka

**Кластеры:**

- Primary: 3 брокера (kafka-primary-0,1,2) - основной кластер
- Secondary: 3 брокера (kafka-secondary-0,1,2) - для аналитики

**Репликация:**
MirrorMaker2 реплицирует данные из Primary в Secondary.

**Шифрование и аутентификация:**

- SSL (TLS) для всех соединений с брокерами
- SASL PLAIN для аутентификации пользователей

**Топики в Primary:**

- `items-raw` - сырые данные товаров от shop-api (3 партиции, RF=3)
- `items-validated` - валидированные товары (3 партиции, RF=3)
- `items-banned` - забаненные товары (3 партиции, RF=3, compacted)
- `client-search-requests` - запросы поиска от клиентов (3 партиции, RF=3)
- `client-recommendations` - рекомендации пользователям (3 партиции, RF=3, compacted)

**Пользователи и ACL:**

- `admin` - полные права на оба кластера
- `shop-api` - Write в items-raw
- `client-api` - Write в client-search-requests
- `items-validator` - Read items-raw, Write/Read items-banned, Write items-validated
- `analytics` - Read client-search-requests (secondary), Write client-recommendations (secondary)

**Мониторинг**

- Через JMX-экспортеры происходит сбор метрик в Prometheus.
- Визуализация данных настроена через Grafana.
- Настроены алерты на недоступность брокера.

### Добавление товаров

**Shop API → Kafka**
- Shop API принимает POST запросы (`/items/add`) с данными товаров и отправляет товары в топик `items-raw`.
- Можно использовать UI - товары предзаполняются в поле ввода из файла `data/items.json`. Можно редактировать как файл, так и поле ввода.
- Для продюсера настроено использование SSL, SASL аутентификация. Добавлена интеграция с Schema Registry. Установлена конфигурация acks=all для подтверждения записи, т.к. важно гарантировать доставку.

**Kafka → Items Validator -> Kafka**
- Faust приложение использует два агента - для валидации товаров и управления блокировкой товаров.
- Агент управления блокировкой обновляет таблицу заблокированных товаров при добавлении сообщений в `items-banned`. Сам топик `items-banned` настроен как compacted, т.к. важно только последнее сообщение по ключу. Таблица и топик ко-партиционированы с топиком исходных товаров `items-raw` через ключ - название товаров. 
- Заблокированными товарами можно управлять через UI. Для Faust настроено REST API
    - `/api/banned/add` - добавление товара в топик `items-banned` с пометкой о блокировке
    - `/api/banned/remove/` - добавление товара в `items-banned` с пометкой о разблокировке
    - `/api/banned/list/` - чтение заблокированных товаров из changelog таблицы. 
- Агент валидации проверяет товар по таблице при добавлении сообщений в `items-raw`. Если товар не забанен - пишет в `items-validated`. Если забанен - игнорирует. Товары блокируются по полному совпадению имени.
- Настроено: SSL/SASL для подключения к Kafka, интеграция с Schema Registry через Faust Codec.

**Kafka → Kafka Connect → Elasticsearch**
- Elasticsearch Sink Connector читает провалидированные товары из `items-validated` и индексирует в Elasticsearch.
- Настроено: SSL/SASL подключение к Kafka, интеграция с Schema Registry, connection.url для Elasticsearch, автоматическое создание индекса (`items-validated`).
- Elasticsearch хранит товары в индексе для полнотекстового поиска.
- Настроена Kibana для визуализации и поиска (индекс `items-validated`).

### Поиск товаров и рекомендации

**Client API → Elasticsearch, Kafka, ksqlDB**
- Client API принимает поисковые запросы от клиентов. Запросы можно выполнять тоже через UI (GET `/items/search`). Можно искать не только по названию, но и по любой информации о товаре (категория, описание итд), т.к. поиск идет в Elasticsearch.
- Выполняет поиск по товарам в Elasticsearch и помимо выдачи ответа отправляет запрос пользователя и результаты поиска в топик `client-search-requests`.
- Так же позволяет запрашивать рекомендации товаров для пользователя (GET `/items/recommend`). Запрашивает данные из ksqlDB таблицы. Подробности см. далее.
- Конфигурация: SSL/SASL, интеграция с Schema Registry.
- В отличие от Shop API продюсера не ждет подтверждения доставки, т.к. аналитика не так критична для данного приложения.

**Kafka → MirrorMaker2 → Kafka (Secondary)**
- MirrorMaker2 реплицирует данные Primary кластера в Secondary кластер. Настроено: SSL/SASL для обоих кластеров, exactly-once семантика, автоматическая репликация ACL и конфигураций.

**Kafka (Secondary) → Analytics (Spark Streaming) -> Kafka (Secondary)**
- Spark Streaming читает `client-search-requests` из Secondary кластера. Выполняет "аналитику" в режиме реального времени (микробатчинг).
- Фильтрует запросы без найденных товаров.
- Если товары были по запросу найдены - сохраняет последний результат как рекомендацию для пользователя.
- Добавлена интеграция с Schema Registry.
- Используется HDFS для Spark checkpoint'ов (hdfs://hadoop-namenode:9000/spark/checkpoints/analytics).
- При желании можно хранить в HDFS и данные по запросам, тогда можно будет делать аналитику не только в реальном времени, но и с использованием исторических данных.
- Рекомендации записываются в топик `client-recommendations`.

**Kafka (Secondary) → ksqlDB**
- ksqlDB создает stream `client_recommendations_stream` поверх топика `client-recommendations` и таблицу `client_recommendations_table` с агрегацией LATEST_BY_OFFSET по user_id. Настроено: SSL/SASL подключение, JSON_SR формат для работы со Schema Registry.
- Таблица доступна для SQL-запросов в реальном времени.
- Топик рекомендаций compact, т.к. интересуют только актуальные рекомендации для пользователя.
- Client API читает данные из таблицы (описано ранее).
