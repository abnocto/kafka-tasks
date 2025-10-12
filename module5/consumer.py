from confluent_kafka import Consumer as KafkaConsumer

# Настройки ACL см. в README.md (Авторизация)
class Consumer:
    def __init__(self):
        self.kafka_consumer = KafkaConsumer({
            # Kafka
            "bootstrap.servers": "localhost:9094,localhost:9095,localhost:9096",
            "group.id": "consumer",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True,
            "session.timeout.ms": 6000,
            "security.protocol": "SASL_SSL", # Комбинация SASL и SSL
            
            # SSL
            "ssl.ca.location": "ca/ca.crt",  # Сертификат CA
            "ssl.certificate.location": "kafka-0-creds/kafka.crt",  # Сертификат клиента Kafka (для упрощения используем сертификат для kafka-0 чтобы не создавать отдельный клиентский сертификат)
            "ssl.key.location": "kafka-0-creds/kafka.key",  # Приватный ключ для клиента Kafka (для упрощения используем ключ для kafka-0 чтобы не создавать отдельный клиентский сертификат)

            # SASL
            "sasl.mechanism": "PLAIN", # Механизм аутентификации SASL/PLAIN
            "sasl.username": "client-consumer", # Имя пользователя
            "sasl.password": "client-consumer-secret", # Пароль
        })
    
    def run(self):
        try:
            self.kafka_consumer.subscribe(['topic-1'])

            while True:
                message = self.kafka_consumer.poll(timeout=1)

                if not message:
                    continue;

                if message.error():
                    print(f'Ошибка получения сообщения: {message.error()}')
                    continue

                print(f'Сообщение: {message.value()} получено из топика {message.topic()}, партиция {message.partition()}, смещение {message.offset()}.')

        except Exception as e:
            print(f'Ошибка цикла чтения сообщений: {e}')

        finally:    
            self.kafka_consumer.close()

def main():
    consumer = Consumer()
    consumer.run()

if __name__ == "__main__":
    main()