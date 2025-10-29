import logging

from confluent_kafka import Producer as KafkaProducer
from confluent_kafka.serialization import SerializationContext, MessageField

from app.schema import client_search_request_serializer

logger = logging.getLogger(__name__)

class Producer:
    def __init__(self):
        self.kafka_producer = KafkaProducer({
            "bootstrap.servers": "kafka-primary-0:9092,kafka-primary-1:9092,kafka-primary-2:9092",
            "acks": "0",
            "security.protocol": "SASL_SSL",
            
            "ssl.ca.location": "/ssl/ca.crt",
                    
            "sasl.mechanism": "PLAIN",
            "sasl.username": "client-api",
            "sasl.password": "client-api-secret", 
        })

        self.topic_name = 'client-search-requests'
    
    def send_client_search_request(self, client_search_request):
        try:
            key = str(client_search_request.get('user_id', ''))
                
            value = client_search_request_serializer(
                client_search_request,
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
