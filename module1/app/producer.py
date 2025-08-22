import random
import time
import logging
import os

from confluent_kafka import Producer as KafkaProducer
from confluent_kafka.serialization import SerializationContext, MessageField

from app.item import Item
from app.schema import items_serializer

logger = logging.getLogger(__name__)

class Producer:
    def __init__(self):
        self.producer = KafkaProducer({
            # Сервера кластера
            "bootstrap.servers": os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
            # Подтверждение доставки сообщения только после того, как оно будет записано в лидера
            "acks": "1",
            # Максимальное количество попыток отправки сообщения
            "retries": 3,
        })

        self.topic_name = 'items'

    # Основной цикл отправки сообщений
    def run(self):
        while True:
            try:
                # Генерируем случайный экземпляр Item
                item = Item.generate()

                # Сериализуем Item
                serialized_item = items_serializer(item, SerializationContext(self.topic_name, MessageField.VALUE))
                logger.info(f'Отправляем сообщение: {serialized_item}')

                # Выбираем случайную партицию
                topic_partition = random.randint(0, 2)

                # Отправляем сообщение в топик
                self.producer.produce(
                    self.topic_name,
                    key=str(topic_partition),
                    value=serialized_item,
                    partition=topic_partition,
                    callback=self.__message_delivery_callback
                )

                # Ожидаем доставки сообщения
                self.producer.flush(timeout=10)
            
            except Exception as e:
                logger.error(f'Ошибка цикла отправки сообщений: {e}')

            finally:    
                # Ждем случайное время перед отправкой следующего сообщения
                time.sleep(random.random())

    # Обработчик доставки сообщения
    def __message_delivery_callback(self, error, message) -> None:
        if error is not None:
            logger.error(f'Ошибка доставки сообщения: {error.str()}')
        else:
            logger.info(f'OK: сообщение доставлено в топик {message.topic()}, партиция {message.partition()}, смещение {message.offset()}.')
