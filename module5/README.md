## Предварительная подготовка

- Настроим `docker-compose.yml` с тремя kafka брокерами и kafka-ui (можно взять из `module-1`)

- Напишем простые продюсер и консюмер (тоже можно взять из прошлых модулей)

## Шифрование

### 1. Создание файла конфигурации для корневого сертификата (Root CA)

- Создадим директорию `ca`
- Создадим файл `ca.cnf`:

```
[ policy_match ]
countryName = match
stateOrProvinceName = match
organizationName = match
organizationalUnitName = optional
commonName = supplied
emailAddress = optional


[ req ]
prompt = no
distinguished_name = dn
default_md = sha256
default_bits = 4096
x509_extensions = v3_ca


[ dn ]
countryName = RU
organizationName = Yandex
organizationalUnitName = Practice
localityName = Moscow
commonName = yandex-practice-kafka-ca


[ v3_ca ]
subjectKeyIdentifier = hash
basicConstraints = critical,CA:true
authorityKeyIdentifier = keyid:always,issuer:always
keyUsage = critical,keyCertSign,cRLSign
```

### 2. Создание корневого сертификата и ключа

```bash
openssl req -new \
    -nodes \
    -x509 \
    -days 365 \
    -newkey rsa:2048 \
    -keyout ca/ca.key \
    -out ca/ca.crt \
    -config ca/ca.cnf
```

- Объединим ключ и сертификат в `ca.pem` файл

```bash
cat ca/ca.crt ca/ca.key > ca/ca.pem
```

### Шаги 3-9 нужно выполнить для каждого брокера (kafka-0, kafka-1, kafka-2):

- Далее инструкция для kafka-0

### 3. Cоздание конфигурационного файла

- Создадим директорию `kafka-0-creds`
- Создадим в ней файл `kafka.cnf`:

```
[req]
prompt = no
distinguished_name = dn
default_md = sha256
default_bits = 4096
req_extensions = v3_req


[ dn ]
countryName = RU
organizationName = Yandex
organizationalUnitName = Practice
localityName = Moscow
commonName = kafka-0


[ v3_ca ]
subjectKeyIdentifier = hash
basicConstraints = critical,CA:true
authorityKeyIdentifier = keyid:always,issuer:always
keyUsage = critical,keyCertSign,cRLSign


[ v3_req ]
subjectKeyIdentifier = hash
basicConstraints = CA:FALSE
nsComment = "OpenSSL Generated Certificate"
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = @alt_names


[ alt_names ]
DNS.1 = kafka-0
DNS.2 = kafka-0-external
DNS.3 = localhost
```

### 4. Создание приватного ключа и запроса на сертификат

```bash
openssl req -new \
    -newkey rsa:2048 \
    -keyout kafka-0-creds/kafka.key \
    -out kafka-0-creds/kafka.csr \
    -config kafka-0-creds/kafka.cnf \
    -nodes
```

### 5. Создание и подпись сертификата

```bash
openssl x509 -req \
    -days 3650 \
    -in kafka-0-creds/kafka.csr \
    -CA ca/ca.crt \
    -CAkey ca/ca.key \
    -CAcreateserial \
    -out kafka-0-creds/kafka.crt \
    -extfile kafka-0-creds/kafka.cnf \
    -extensions v3_req
```

### 6. Создание PKCS12 хранилища

```bash
openssl pkcs12 -export \
    -in kafka-0-creds/kafka.crt \
    -inkey kafka-0-creds/kafka.key \
    -chain \
    -CAfile ca/ca.pem \
    -name kafka-0 \
    -out kafka-0-creds/kafka.p12 \
    -passout pass:kafka-password
```

### 7. Создание keystore

```bash
keytool -importkeystore \
    -srckeystore kafka-0-creds/kafka.p12 \
    -srcstoretype PKCS12 \
    -srcstorepass kafka-password \
    -destkeystore kafka-0-creds/kafka.keystore.jks \
    -deststoretype JKS \
    -deststorepass kafka-password \
    -noprompt
```

### 8. Создание truststore

```bash
keytool -import \
    -file ca/ca.crt \
    -alias ca \
    -keystore kafka-0-creds/kafka.truststore.jks \
    -storepass kafka-password \
    -noprompt
```

### 9. Дополнение конфигурации в `docker-compose.yml`

```yml
    ...
    environment:
        ...
        - KAFKA_CFG_LISTENERS=BROKER://:9092,CONTROLLER://:9093,EXTERNAL://:9094
        - KAFKA_CFG_ADVERTISED_LISTENERS=BROKER://kafka-0:9092,EXTERNAL://localhost:9094
        - KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP=BROKER:SSL,CONTROLLER:SSL,EXTERNAL:SSL

        - KAFKA_CFG_SSL_KEYSTORE_LOCATION=/bitnami/kafka/config/certs/kafka.keystore.jks
        - KAFKA_CFG_SSL_KEYSTORE_PASSWORD=kafka-password
        - KAFKA_CFG_SSL_KEY_PASSWORD=kafka-password
        - KAFKA_CFG_SSL_TRUSTSTORE_LOCATION=/bitnami/kafka/config/certs/kafka.truststore.jks
        - KAFKA_CFG_SSL_TRUSTSTORE_PASSWORD=kafka-password
    volumes:
        ...
        - ./kafka-0-creds:/bitnami/kafka/config/certs
```

### 10. Для kafka-ui: дополнение конфигурации в `docker-compose.yml`

```yml
    ...
    environment:
        ...
        - KAFKA_CLUSTERS_0_PROPERTIES_SECURITY_PROTOCOL=SSL

        - KAFKA_CLUSTERS_0_PROPERTIES_SSL_KEYSTORE_LOCATION=/tmp/kafka.keystore.jks
        - KAFKA_CLUSTERS_0_PROPERTIES_SSL_KEYSTORE_PASSWORD=kafka-password
        - KAFKA_CLUSTERS_0_PROPERTIES_SSL_KEY_PASSWORD=kafka-password
        - KAFKA_CLUSTERS_0_PROPERTIES_SSL_TRUSTSTORE_LOCATION=/tmp/kafka.truststore.jks
        - KAFKA_CLUSTERS_0_PROPERTIES_SSL_TRUSTSTORE_PASSWORD=kafka-password
    volumes:
        ...
        - ./kafka-0-creds:/tmp
```

### 10. Для продюсера и консьюмера: дополнение конфигурации

```python
    ...
    "security.protocol": "SSL",
    "ssl.ca.location": "ca/ca.crt",  # Сертификат CA
    "ssl.certificate.location": "kafka-0-creds/kafka.crt",  # Сертификат клиента Kafka (для упрощения используем сертификат kafka-0)
    "ssl.key.location": "kafka-0-creds/kafka.key",  # Приватный ключ для клиента Kafka (для упрощения используем ключ kafka-0)
```

## Аутентификация

- Нужно выполнить все шаги из предущего раздела, т.к. будем настраивать SSL + SASL/PLAIN

### 1. Для каждого брокера - дополнение конфигурации в `docker-compose.yml`

- Для bitnami образа не нужен отдельный файл `jaas.conf`, все делаем через параметры конфигурации

- Будут три пользователя - админ, клиент-продюсер, клиент-консюмер

```yml
    ...
    environment:
        ...
        - KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP=BROKER:SASL_SSL,CONTROLLER:SASL_SSL,EXTERNAL:SASL_SSL

        - KAFKA_CFG_SASL_ENABLED_MECHANISMS=PLAIN
        - KAFKA_CFG_SASL_MECHANISM_INTER_BROKER_PROTOCOL=PLAIN
        - KAFKA_CFG_SASL_MECHANISM_CONTROLLER_PROTOCOL=PLAIN
        - KAFKA_CLIENT_USERS=admin,client-producer,client-consumer
        - KAFKA_CLIENT_PASSWORDS=admin-secret,client-producer-secret,client-consumer-secret
        - KAFKA_INTER_BROKER_USER=admin
        - KAFKA_INTER_BROKER_PASSWORD=admin-secret
        - KAFKA_CONTROLLER_USER=admin
        - KAFKA_CONTROLLER_PASSWORD=admin-secret
```

### 2. Для kafka-ui: дополнение конфигурации в `docker-compose.yml`

```yml
    ...
    environment:
        ...
        - KAFKA_CLUSTERS_0_PROPERTIES_SECURITY_PROTOCOL=SASL_SSL

        - KAFKA_CLUSTERS_0_PROPERTIES_SASL_MECHANISM=PLAIN
        - KAFKA_CLUSTERS_0_PROPERTIES_SASL_JAAS_CONFIG=org.apache.kafka.common.security.plain.PlainLoginModule required username="admin" password="admin-secret";
```

### 3. Для продюсера - дополнение конфигурации

```python
    ...
    "security.protocol": "SASL_SSL", # Комбинация SASL и SSL
    ...
    "sasl.mechanism": "PLAIN", # Механизм аутентификации SASL/PLAIN
    "sasl.username": "client-producer", # Имя пользователя
    "sasl.password": "client-producer-secret", # Пароль
```

### 4. Для консюмера - дополнение конфигурации

```python
    ...
    "security.protocol": "SASL_SSL", # Комбинация SASL и SSL
    ...
    "sasl.mechanism": "PLAIN", # Механизм аутентификации SASL/PLAIN
    "sasl.username": "client-consumer", # Имя пользователя
    "sasl.password": "client-consumer-secret", # Пароль
```

## Авторизация

- Тоже нужно выполнить все шаги из предущих разделов, в итоге будет SSL + SASL + ACL

### 1. Для каждого брокера - дополнение конфигурации в `docker-compose.yml`

```yml
    ...
    environment:
        ...
        - KAFKA_CFG_AUTHORIZER_CLASS_NAME=org.apache.kafka.metadata.authorizer.StandardAuthorizer
        - KAFKA_CFG_ALLOW_EVERYONE_IF_NO_ACL_FOUND=false
        - KAFKA_CFG_SUPER_USERS=User:admin
```

### 2. Добавление для kafka-0 конфига для возможности работы через CLI утилиты, т.к. теперь есть SSL + SASL + ACL

- Добавим конфиг для контейнера

```bash
docker exec -it $(docker compose ps -q kafka-0) bash -c '
cat > /tmp/client.properties <<EOF
security.protocol=SASL_SSL

ssl.truststore.location=/bitnami/kafka/config/certs/kafka.truststore.jks
ssl.truststore.password=kafka-password

sasl.mechanism=PLAIN
sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required username="admin" password="admin-secret";
EOF'
```

- Далее для CLI команд нужно указывать параметр `--command-config /tmp/client.properties`

### 3. Проверка настроек авторизации перед добавлением ACL

- Просмотрим ACL, должен быть пустой список

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-acls.sh \
    --bootstrap-server localhost:9092 \
    --command-config /tmp/client.properties \
    --list
```

- Создадим топики `topic-1` и `topic-2` для проверки авторизации

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-topics.sh \
    --bootstrap-server localhost:9092 \
    --command-config /tmp/client.properties \
    --create \
    --topic topic-1 \
    --partitions 1 \
    --replication-factor 1

docker exec -it $(docker compose ps -q kafka-0) kafka-topics.sh \
    --bootstrap-server localhost:9092 \
    --command-config /tmp/client.properties \
    --create \
    --topic topic-2 \
    --partitions 1 \
    --replication-factor 1
```

- Продюсер и консюмер должны возвращать ошибки при попытке чтения и записи

```bash
python3 producer.py
python3 consumer.py
```

### 4. Добавление разрешений пользователю `client-producer`

- На запись - для топика `topic-1` (Write)
- На запись - для топика `topic-2` (Write)

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-acls.sh \
    --bootstrap-server localhost:9092 \
    --command-config /tmp/client.properties \
    --add \
    --allow-principal User:client-producer \
    --operation Write \
    --topic topic-1

docker exec -it $(docker compose ps -q kafka-0) kafka-acls.sh \
    --bootstrap-server localhost:9092 \
    --command-config /tmp/client.properties \
    --add \
    --allow-principal User:client-producer \
    --operation Write \
    --topic topic-2
```

- Проверим, что продюсер теперь выполняет запись без ошибок, но консюмер все еще получает ошибки доступа.

### 5. Добавление разрешений пользователю `client-consumer`

- На чтение и получение информации - для топика `topic-1` (Read, Describe)
- На чтение и получение информации - для группы `consumer` (Read, Describe)

```bash
docker exec -it $(docker compose ps -q kafka-0) kafka-acls.sh \
    --bootstrap-server localhost:9092 \
    --command-config /tmp/client.properties \
    --add \
    --allow-principal User:client-consumer \
    --operation Read \
    --topic topic-1

docker exec -it $(docker compose ps -q kafka-0) kafka-acls.sh \
    --bootstrap-server localhost:9092 \
    --command-config /tmp/client.properties \
    --add \
    --allow-principal User:client-consumer \
    --operation Describe \
    --topic topic-1

docker exec -it $(docker compose ps -q kafka-0) kafka-acls.sh \
    --bootstrap-server localhost:9092 \
    --command-config /tmp/client.properties \
    --add \
    --allow-principal User:client-consumer \
    --operation Read \
    --group consumer

docker exec -it $(docker compose ps -q kafka-0) kafka-acls.sh \
    --bootstrap-server localhost:9092 \
    --command-config /tmp/client.properties \
    --add \
    --allow-principal User:client-consumer \
    --operation Describe \
    --group consumer
```

- Проверим, что консюмер теперь выполняет чтение из `topic-1` без ошибок, но если попытаться читать из `topic-2`, будет ошибка.

- Список ACL выглядит следующим образом

```
Current ACLs for resource `ResourcePattern(resourceType=GROUP, name=consumer, patternType=LITERAL)`:
        (principal=User:client-consumer, host=*, operation=DESCRIBE, permissionType=ALLOW)
        (principal=User:client-consumer, host=*, operation=READ, permissionType=ALLOW)

Current ACLs for resource `ResourcePattern(resourceType=TOPIC, name=topic-2, patternType=LITERAL)`:
        (principal=User:client-producer, host=*, operation=WRITE, permissionType=ALLOW)

Current ACLs for resource `ResourcePattern(resourceType=TOPIC, name=topic-1, patternType=LITERAL)`:
        (principal=User:client-producer, host=*, operation=WRITE, permissionType=ALLOW)
        (principal=User:client-consumer, host=*, operation=READ, permissionType=ALLOW)
        (principal=User:client-consumer, host=*, operation=DESCRIBE, permissionType=ALLOW)
```
