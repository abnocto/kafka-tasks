import os
import faust

# Конфигурация Faust приложения
message_app = faust.App(
    "message-app",
    broker=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
    value_serializer="json",
)
