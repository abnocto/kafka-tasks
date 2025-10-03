from confluent_kafka import Consumer as KafkaConsumer
from confluent_kafka.serialization import SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer

class Consumer:
    def __init__(self):
        self.kafka_consumer = KafkaConsumer({
            "bootstrap.servers": "localhost:9094,localhost:9095,localhost:9096",
            "group.id": "consumer",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True,
            'session.timeout.ms': 6000
        })

        self.schema_registry_client = SchemaRegistryClient({
            "url": "http://localhost:8081"
        })

        self.message_value_deserializer = AvroDeserializer(
            schema_registry_client=self.schema_registry_client
        )
    
    def run(self):
        try:
            self.kafka_consumer.subscribe([
                'module4.public.users',
                'module4.public.orders'
            ])

            while True:
                message = self.kafka_consumer.poll(timeout=1)

                if not message:
                    continue;

                if message.error():
                    print(f'Ошибка получения сообщения: {message.error()}')
                    continue

                message_value = self.message_value_deserializer(
                    message.value(),
                    SerializationContext(message.topic(), MessageField.VALUE)
                )

                print(f'Сообщение: {message_value} получено из топика {message.topic()}, партиция {message.partition()}, смещение {message.offset()}.')

        except Exception as e:
            print(f'Ошибка цикла чтения сообщений: {e}')

        finally:    
            self.kafka_consumer.close()

def main():
    consumer = Consumer()
    consumer.run()

if __name__ == "__main__":
    main()