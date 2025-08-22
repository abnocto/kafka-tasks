import logging
import os

from confluent_kafka import Consumer as KafkaConsumer
from confluent_kafka.serialization import SerializationContext, MessageField

from app.schema import items_deserializer

logger = logging.getLogger(__name__)

class BatchMessageConsumer:
    def __init__(self):
        self.consumer = KafkaConsumer({ 
            # Сервера кластера
            "bootstrap.servers": os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
            # Идентификатор группы консьюмеров
            "group.id": "batch",
            # Сразу читаем все сообщения с начала топика
            "auto.offset.reset": "earliest",
            # Автоматически НЕ коммитим offset после чтения сообщения
            "enable.auto.commit": False, 
            # Минимальный размер батча для накопления
            "fetch.min.bytes": 2000,
            # Максимальный таймаут ожидания накопления данных
            "fetch.wait.max.ms": 5000,
            # Таймаут сессии
            "session.timeout.ms": 6000,
        })

        self.topic_name = 'items'

        self.batch_size = 10
    
    # Основной цикл чтения сообщений
    def run(self):
        try:
            # Подписываемся на топик
            self.consumer.subscribe([self.topic_name])
            
            while True:
                # Выполняем опрос батча сообщений
                messages = self.consumer.consume(num_messages=self.batch_size, timeout=5)

                if not messages:
                    continue

                # Обрабатываем только полные батчи
                if len(messages) < self.batch_size:
                    logger.info(f'Получено {len(messages)} сообщений, ожидаем полный батч ({self.batch_size})')
                    continue

                logger.info(f'Получен полный батч: {len(messages)} сообщений')
                
                # Обрабатываем каждое сообщение в батче
                for message in messages:
                    if message.error():
                        logger.error(f'Ошибка получения сообщения: {message.error()}')
                        continue

                    value = message.value()

                    # Десериализуем сообщение
                    item = items_deserializer(value, SerializationContext(self.topic_name, MessageField.VALUE))

                    logger.info(f'Сообщение: {item} получено из топика {message.topic()}, партиция {message.partition()}, смещение {message.offset()}.')

                # Синхронно коммитим после обработки всего батча
                self.consumer.commit(asynchronous=False)

                logger.info(f'Батч обработан')

        except Exception as e:
            logger.error(f'Ошибка цикла чтения сообщений: {e}')

        finally:    
            self.consumer.close()
