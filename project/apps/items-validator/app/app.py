import ssl
import faust

ssl_context = ssl.create_default_context(
    purpose=ssl.Purpose.SERVER_AUTH,
    cafile="/ssl/ca.crt",
)

items_validator_app = faust.App(
    "items-validator-app",
    broker="kafka://kafka-primary-0:9092,kafka-primary-1:9092,kafka-primary-2:9092",

    broker_credentials=faust.SASLCredentials(
        ssl_context=ssl_context,
        mechanism="PLAIN",
        username="items-validator",
        password="items-validator-secret",
    ),
    
    web_port=8888,
)
