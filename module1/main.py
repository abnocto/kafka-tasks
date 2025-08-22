import logging
import multiprocessing
import signal

from app.producer import Producer
from app.consumer_single import SingleMessageConsumer
from app.consumer_batch import BatchMessageConsumer

logging.basicConfig(
    level=logging.INFO,
    format='%(name)s | %(levelname)s | %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

def run_producer():
    try:
        producer = Producer()
        producer.run()

    except Exception as e:
        logger.error(f'Ошибка в процессе producer: {e}')

def run_single_message_consumer():
    try:
        single_message_consumer = SingleMessageConsumer()
        single_message_consumer.run()

    except Exception as e:
        logger.error(f'Ошибка в процессе single-message-consumer: {e}')

def run_batch_message_consumer():
    try:
        batch_message_consumer = BatchMessageConsumer()
        batch_message_consumer.run()

    except Exception as e:
        logger.error(f'Ошибка в процессе batch-message-consumer: {e}')

class Main:
    def __init__(self):
        logger.info('Старт приложения')

        self.processes = []

        signal.signal(signal.SIGTERM, self.__signal_handler)
        signal.signal(signal.SIGINT, self.__signal_handler)

    def run(self):
        try:
            self.processes = [
                multiprocessing.Process(name='producer', target=run_producer),
                multiprocessing.Process(name='single-message-consumer', target=run_single_message_consumer),
                multiprocessing.Process(name='batch-message-consumer', target=run_batch_message_consumer)
            ]
            
            for process in self.processes:
                process.start()
                logger.info(f'Процесс {process.name} запущен с PID: {process.pid}')

            for process in self.processes:
                process.join()

        except KeyboardInterrupt:
            logger.info('Прерывание приложения...')
            self.stop()
            
        except Exception as e:
            logger.error(f'Ошибка в главном процессе: {e}')
            self.stop()

    def __signal_handler(self, signum, frame):
        signal_name = 'SIGTERM' if signum == signal.SIGTERM else 'SIGINT'
        logger.info(f'Получен сигнал {signal_name}. Прерывание приложения...')
        self.stop()

    def stop(self):
        for process in self.processes:
            if process.is_alive():
                process.terminate()
                process.join()

        logger.info('Приложение остановлено')

if __name__ == '__main__':
    main = Main()
    main.run()