import logging

from confluent_kafka import Producer as KafkaProducer
from confluent_kafka.serialization import SerializationContext, MessageField

from app.schema import items_raw_serializer

logger = logging.getLogger(__name__)

class Producer:
    def __init__(self):
        self.kafka_producer = KafkaProducer({
            "bootstrap.servers": "kafka-primary-0:9092,kafka-primary-1:9092,kafka-primary-2:9092",
            "acks": "all",
            "retries": 3,
            "security.protocol": "SASL_SSL",
            
            "ssl.ca.location": "/ssl/ca.crt",
            
            "sasl.mechanism": "PLAIN",
            "sasl.username": "shop-api",
            "sasl.password": "shop-api-secret", 
        })

        self.topic_name = 'items-raw'
    
    def send_items(self, items):
        for item_raw in items:
            try:
                key = str(item_raw.get('name', ''))
                
                value = items_raw_serializer(
                    item_raw,
                    SerializationContext(self.topic_name, MessageField.VALUE)
                )
                
                self.kafka_producer.produce(
                    self.topic_name,
                    key=key,
                    value=value,
                    callback=self.__message_delivery_callback
                )

                self.kafka_producer.flush(timeout=10)
                
            except Exception as e:
                logger.error(f'Ошибка отправки сообщения: {e}')
    
    def __message_delivery_callback(self, error, message) -> None:
        if error is not None:
            logger.error(f"Ошибка доставки: {error}")
        else:
            logger.info(f"OK: сообщение доставлено в {message.topic()}, партиция {message.partition()}, смещение {message.offset()}")
