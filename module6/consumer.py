import requests

from confluent_kafka import Consumer as KafkaConsumer
from confluent_kafka.serialization import SerializationContext, MessageField

from schema import AnalyticsEvent, analytics_event_deserializer

class Consumer:
    def __init__(self):
        self.kafka_consumer = KafkaConsumer({
            "bootstrap.servers": "rc1a-nb6125776ku65anj.mdb.yandexcloud.net:9091,rc1b-lbl8a7apd2gi7lni.mdb.yandexcloud.net:9091,rc1d-tsglq1hehj5vkbm2.mdb.yandexcloud.net:9091",
            "group.id": "consumer",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True,
            "session.timeout.ms": 6000,
            "security.protocol": "SASL_SSL",
            
            "ssl.ca.location": "ca/yandex.crt",

            "sasl.mechanism": "SCRAM-SHA-512",
            "sasl.username": "analytics-events-consumer",
            "sasl.password": "analytics-events-consumer-password",
        })
        
        self.hdfs_namenode_url = 'https://localhost:9871'
    
    def run(self):
        try:
            self.kafka_consumer.subscribe(['analytics-events'])

            while True:
                message = self.kafka_consumer.poll(timeout=1)

                if not message:
                    continue;

                if message.error():
                    print(f'Ошибка получения сообщения: {message.error()}')
                    continue

                analytics_event = analytics_event_deserializer(message.value(), SerializationContext(message.topic(), MessageField.VALUE))

                print('\n')
                print(f'Сообщение: {analytics_event} получено из топика {message.topic()}, партиция {message.partition()}, смещение {message.offset()}.')

                # Здесь для примера интеграции HDFS с Kafka просто сохраняем и читаем файл синхронно
                # Для production это не подойдет, т.к. заблокирует чтение из Kafka до завершения сохранения в HDFS
                # Лучше использовать Kafka Connect (HDFS Sink Connector), батчинг-обработку, асинхронную запись итд
                hdfs_file_path = self.get_hdfs_file_path(analytics_event)
                hdfs_username = 'kafka-consumer'
                
                self.create_hdfs_file(hdfs_file_path, hdfs_username, str(analytics_event))
                print(f'Файл сохранен в HDFS: {hdfs_file_path}', f'пользователь: {hdfs_username}')

                hdfs_file_content = self.read_hdfs_file(hdfs_file_path, hdfs_username)
                print(f'Файл прочитан из HDFS: {hdfs_file_content}', f'пользователь: {hdfs_username}')

        except Exception as e:
            print(f'Ошибка цикла чтения сообщений: {e}')

        finally:    
            self.kafka_consumer.close()


    def get_hdfs_file_path(self, analytics_event: AnalyticsEvent) -> str:
        return f'/analytics/events/id_{analytics_event.id}'

    def create_hdfs_file(self, hdfs_path: str, hdfs_user: str, data: str) -> None:
        create_operation_response = requests.put(
            f'{self.hdfs_namenode_url}/webhdfs/v1{hdfs_path}?op=CREATE&overwrite=true&user.name={hdfs_user}',
            allow_redirects=False,
            verify='hadoop/creds/ca.crt'
        )

        if create_operation_response.status_code != 307:
            raise Exception(f'Ошибка (create operation): {create_operation_response.status_code} - {create_operation_response.text}')

        response = requests.put(
            create_operation_response.headers['Location'],
            data=data,
            verify='hadoop/creds/ca.crt'
        )
        
        if response.status_code != 201:
            raise Exception(f'Ошибка (write operation): {response.status_code} - {response.text}')

    def read_hdfs_file(self, hdfs_path: str, hdfs_user: str) -> str:
        open_operation_response = requests.get(
            f'{self.hdfs_namenode_url}/webhdfs/v1{hdfs_path}?op=OPEN&user.name={hdfs_user}',
            allow_redirects=False,
            verify='hadoop/creds/ca.crt'
        )
        
        if open_operation_response.status_code != 307:
            raise Exception(f'Ошибка (open operation): {open_operation_response.status_code} - {open_operation_response.text}')

        response = requests.get(
            open_operation_response.headers['Location'],
            verify='hadoop/creds/ca.crt'
        )
        
        if response.status_code != 200:
            raise Exception(f'Ошибка (read operation): {response.status_code} - {response.text}')

        return response.text

def main():
    consumer = Consumer()
    consumer.run()

if __name__ == "__main__":
    main()