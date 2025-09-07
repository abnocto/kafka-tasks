### Запуск инфраструктуры
```bash
docker compose up -d kafka-0 kafka-1 kafka-2 kafka-ui
```

### Создание топиков
```bash
# сообщения
docker exec -it $(docker compose ps -q kafka-0) kafka-topics.sh --bootstrap-server kafka-0:9092 --create --topic messages --partitions 3 --replication-factor 2

# отфильтрованные сообщения
docker exec -it $(docker compose ps -q kafka-0) kafka-topics.sh --bootstrap-server kafka-0:9092 --create --topic filtered-messages --partitions 3 --replication-factor 2

# забанненые пользователи
docker exec -it $(docker compose ps -q kafka-0) kafka-topics.sh --bootstrap-server kafka-0:9092 --create --topic banned-users --partitions 3 --replication-factor 2

# запрещенные слова
docker exec -it $(docker compose ps -q kafka-0) kafka-topics.sh --bootstrap-server kafka-0:9092 --create --topic banned-words --partitions 1 --replication-factor 2
```

### Запуск приложения в трех экземплярах
```bash
docker compose up -d --scale module-2=3 module-2
```

### Проверка статуса
```bash
docker compose ps
```

### Просмотр логов приложения
```bash
docker compose logs -f module-2
```

### Отправка сообщений в соответствующие топики для проверки
```bash
# 1) Пользователь "Bob" отправляет сообщение пользователю "Alice" - отправляется
echo 'Alice:{"sender_id": "Bob", "recipient_id": "Alice", "text": "Привет!"}' | docker exec -i $(docker compose ps -q kafka-0) kafka-console-producer.sh --bootstrap-server kafka-0:9092 --topic messages --property "parse.key=true" --property "key.separator=:"

# 2) Пользователь "Alice" банит пользователя "Bob"
echo 'Alice:{"action": "add", "user_id": "Alice", "banned_user_id": "Bob"}' | docker exec -i $(docker compose ps -q kafka-0) kafka-console-producer.sh --bootstrap-server kafka-0:9092 --topic banned-users --property "parse.key=true" --property "key.separator=:"

# 3) Пользователь "Bob" отправляет сообщение пользователю "Alice" - НЕ отправляется
echo 'Alice:{"sender_id": "Bob", "recipient_id": "Alice", "text": "Привет!"}' | docker exec -i $(docker compose ps -q kafka-0) kafka-console-producer.sh --bootstrap-server kafka-0:9092 --topic messages --property "parse.key=true" --property "key.separator=:"

# 4) Пользователь "Random" отправляет сообщение пользователю "Alice" - отправляется
echo 'Alice:{"sender_id": "Random", "recipient_id": "Alice", "text": "Привет!"}' | docker exec -i $(docker compose ps -q kafka-0) kafka-console-producer.sh --bootstrap-server kafka-0:9092 --topic messages --property "parse.key=true" --property "key.separator=:"

# 5) Пользователь "Alice" разбанивает пользователя "Bob"
echo 'Alice:{"action": "remove", "user_id": "Alice", "banned_user_id": "Bob"}' | docker exec -i $(docker compose ps -q kafka-0) kafka-console-producer.sh --bootstrap-server kafka-0:9092 --topic banned-users --property "parse.key=true" --property "key.separator=:"

# 6) Пользователь "Bob" отправляет сообщение пользователю "Alice" - отправляется
echo 'Alice:{"sender_id": "Bob", "recipient_id": "Alice", "text": "Привет!"}' | docker exec -i $(docker compose ps -q kafka-0) kafka-console-producer.sh --bootstrap-server kafka-0:9092 --topic messages --property "parse.key=true" --property "key.separator=:"

# 7) Добавлено запрещенное слово "запрещенное"
echo 'запрещенное:{"action": "add", "word": "запрещенное"}' | docker exec -i $(docker compose ps -q kafka-0) kafka-console-producer.sh --bootstrap-server kafka-0:9092 --topic banned-words --property "parse.key=true" --property "key.separator=:"

# 8) Пользователь "Bob" отправляет сообщение пользователю "Alice" - отправляется, но замаскировано запрещенное слово
echo 'Alice:{"sender_id": "Bob", "recipient_id": "Alice", "text": "Здесь есть запрещенное слово!"}' | docker exec -i $(docker compose ps -q kafka-0) kafka-console-producer.sh --bootstrap-server kafka-0:9092 --topic messages --property "parse.key=true" --property "key.separator=:"

# 9) Слово "запрещенное" больше не запрещено
echo 'запрещенное:{"action": "remove", "word": "запрещенное"}' | docker exec -i $(docker compose ps -q kafka-0) kafka-console-producer.sh --bootstrap-server kafka-0:9092 --topic banned-words --property "parse.key=true" --property "key.separator=:"

# 10) Пользователь "Bob" отправляет сообщение пользователю "Alice" - отправляется, ничего не замаскировано
echo 'Alice:{"sender_id": 1, "recipient_id": "Alice", "text": "Это уже не запрещенное слово!"}' | docker exec -i $(docker compose ps -q kafka-0) kafka-console-producer.sh --bootstrap-server kafka-0:9092 --topic messages --property "parse.key=true" --property "key.separator=:"
```

### Как работает приложение
* Общее описание
    * При получении сообщения из топика `banned-users` соответствующий агент в зависимости от команды добавляет пользователя в бан или убирает из бана, обновив данные в таблице забаненных пользователей.
    * Аналогично можно добавить или убрать запрещенное слово отправкой сообщения в топик `banned-words` - будут обновлены данные в таблице запрещенных слов.
    * Наконец, агент пользовательских сообщений читает топик `messages`. В случае, если было обнаружено (путем чтения данных из таблицы), что отправитель сообщения был забанен получателем, сообщение далее не обрабатывается. Иначе его подхватывает следующий агент, который выполняет фильтрацию текста сообщения (маскирует запрещенные слова) и отправляет обработанное сообщение в топик `filtered-messages`.

* Работа с таблицей пользователей
    * Изначально мы создали топики `messages`, `filtered-messages`, `banned-users` с тремя партициями каждый.
        * Для таблицы заблокированных пользователей будет тоже автоматически создан топик kafka (changelog).
        * Важно указать, чтобы число партиций для него тоже составляло три.
    * Запускаются воркеры faust приложения. Они составляют одну консьюмер группу. Их тоже три, таким образом каждый воркер будет получать данные из "своей" партиции.
    * Важным моментом является то, с какими ключами отправляются сообщения в топики - соответственно, в какие партиции топиков они попадают.
        * При отправке сообщения в топик `messages` в качестве ключа указывается ид получателя.
        * При отправке сообщения в топик `banned-users` в качестве ключа указывается ид пользователя, который выполняет бан. Это тот же ид получателя.
        * И в таблице забаненных пользователей в качестве ключей мы тоже указываем ид пользователя, который выполняет бан. Тоже ид получателя.
        * Таким образом все данные по конкретному пользователю - получателю сообщений (сообщения, адресованные ему, забаненные им пользователи) будут распределяться в одну и ту же партицию для соответствующих топиков (ко-партиционирование). И с ними будет работать один и тот же воркер.
        * То есть один и тот же воркер и обработает сообщение о бане пользователя конкретным получателем (добавит данные в таблицу у себя локально и в топик kafka), и обработает сообщения из `messages` для этого же ид получателя.
        * В то же время прочие воркеры не будут иметь доступ к данным по этому пользователю, т.к. работают с другими партициями. У них локально не будет доступа к данным из остальных партиций.
        * Если бы мы указывали для `messages` одни ключи, а для блокированных пользователей другие - нарушилось бы ко-партиционирование и обработка данных.

* Работа с таблицей слов
    * Таблица заблокированных слов сделана глобальной.
    * Достаточно одной партиции как в топике `banned-words`, так и в таблице для слов.
    * В то же время все воркеры будут иметь доступ к запрещенным словам (должна выполняться синхронизация локальных данных, по крайней мере во время старта воркеров).
