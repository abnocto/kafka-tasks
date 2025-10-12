import random

from confluent_kafka import Producer as KafkaProducer

from confluent_kafka import Producer as KafkaProducer

# Настройки ACL см. в README.md (Авторизация)
class Producer:
    def __init__(self):
        self.kafka_producer = KafkaProducer({
            # Kafka
            "bootstrap.servers": "localhost:9094,localhost:9095,localhost:9096",
            "acks": "1",
            "retries": 3,
            "security.protocol": "SASL_SSL", # Комбинация SASL и SSL

            # SSL
            "ssl.ca.location": "ca/ca.crt",  # Сертификат CA
            "ssl.certificate.location": "kafka-0-creds/kafka.crt",  # Сертификат клиента Kafka (для упрощения используем сертификат для kafka-0 чтобы не создавать отдельный клиентский сертификат)
            "ssl.key.location": "kafka-0-creds/kafka.key",  # Приватный ключ для клиента Kafka (для упрощения используем ключ для kafka-0 чтобы не создавать отдельный клиентский сертификат)

            # SASL
            "sasl.mechanism": "PLAIN", # Механизм аутентификации SASL/PLAIN
            "sasl.username": "client-producer", # Имя пользователя
            "sasl.password": "client-producer-secret", # Пароль
        })

    def run(self):
        try:
            key = str(random.randint(1, 1000))
            value = 'SSL + SASL + ACL test message: ' + key

            self.kafka_producer.produce(
                'topic-1',
                key=key,   
                value=value,
                callback=self.__message_delivery_callback
            )

            self.kafka_producer.produce(
                'topic-2',
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