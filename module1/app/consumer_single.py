import logging
import os

from confluent_kafka import Consumer as KafkaConsumer
from confluent_kafka.serialization import SerializationContext, MessageField

from app.schema import items_deserializer

logger = logging.getLogger(__name__)

class SingleMessageConsumer:
    def __init__(self):
        self.consumer = KafkaConsumer({ 
            # Сервера кластера
            "bootstrap.servers": os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
            # Идентификатор группы консьюмеров
            "group.id": "single",
            # Сразу читаем все сообщения с начала топика
            "auto.offset.reset": "earliest",
            # Автоматически коммитим offset после чтения сообщения
            "enable.auto.commit": True, 
            # Таймаут сессии
            "session.timeout.ms": 6000,
        })

        self.topic_name = 'items'
    
    # Основной цикл чтения сообщений
    def run(self):
        try:
            # Подписываемся на топик
            self.consumer.subscribe([self.topic_name])
            
            while True:
                # Выполняем опрос сообщений
                message = self.consumer.poll(timeout=1)

                if not message:
                    continue;

                if message.error():
                    logger.error(f'Ошибка получения сообщения: {message.error()}')
                    continue

                value = message.value()

                # Десериализуем сообщение
                item = items_deserializer(value, SerializationContext(self.topic_name, MessageField.VALUE))

                logger.info(f'Сообщение: {item} получено из топика {message.topic()}, партиция {message.partition()}, смещение {message.offset()}.')

        except Exception as e:
            logger.error(f'Ошибка цикла чтения сообщений: {e}')

        finally:    
            self.consumer.close()
