import random
from datetime import datetime

from confluent_kafka import Producer as KafkaProducer
from confluent_kafka.serialization import SerializationContext, MessageField

from schema import AnalyticsEvent, analytics_event_serializer

class Producer:
    def __init__(self):
        self.kafka_producer = KafkaProducer({
            "bootstrap.servers": "rc1a-nb6125776ku65anj.mdb.yandexcloud.net:9091,rc1b-lbl8a7apd2gi7lni.mdb.yandexcloud.net:9091,rc1d-tsglq1hehj5vkbm2.mdb.yandexcloud.net:9091",
            "acks": "1",
            "retries": 3,
            "security.protocol": "SASL_SSL",

            "ssl.ca.location": "ca/yandex.crt",

            "sasl.mechanism": "SCRAM-SHA-512",
            "sasl.username": "analytics-events-producer",
            "sasl.password": "analytics-events-producer-password",
        })

        self.topic_name = 'analytics-events'

    def run(self):
        try:
            analytics_event = AnalyticsEvent(
                id=str(random.randint(1, 1000)),
                type='PageView',
                timestamp=str(datetime.now()),
                serialized_data='a very large piece of data...'
            )

            key = analytics_event.id
            value = analytics_event_serializer(analytics_event, SerializationContext(self.topic_name, MessageField.VALUE))

            self.kafka_producer.produce(
                self.topic_name,
                key=key,   
                value=value,
                callback=self.__message_delivery_callback
            )
            
            self.kafka_producer.flush(timeout=10)
        
        except Exception as e:
            print(f'Ошибка отправки сообщения: {e}')
            

    def __message_delivery_callback(self, error, message) -> None:
        if error is not None:
            print(f'Ошибка доставки сообщения: {error.str()}')
        else:
            print(f'OK: сообщение доставлено в топик {message.topic()}, партиция {message.partition()}, смещение {message.offset()}.')

def main():
    producer = Producer()
    producer.run()

if __name__ == "__main__":
    main()