# rmq_async_worker

Package provides abstractions to create RabbitMQ async worker microservices.

## Example

```python
import pika
import logging
import time
from rmq_async_worker import AsyncWorker, RmqResponseHandler, AckMode

class Worker:
    @classmethod
    def perform(self, msg):
        time.sleep(10)
        logging.info(msg)
        return b'result'

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname) -10s %(asctime)s %(name) -30s %(funcName) -35s %(lineno) -5d: %(message)s'
    )
    AsyncWorker(
        connection_parameters=pika.URLParameters('amqp://guest:guest@localhost:5672/%2F'),
        exchange_params={
            'exchange': 'test_exchange',
            'exchange_type': 'direct',
            'passive': False,
            'durable': True,
            'auto_delete': False
        },
        queue_params={
            'queue': "standard",
            'auto_delete': False
        },
        routing_key='standard_key',
        prefetch_count=2,
        ack_mode=AckMode.ON_RESPOND
    ).start(
        Worker,
        RmqResponseHandler(
            connection_parameters=pika.URLParameters('amqp://guest:guest@localhost:5672/%2F'),
            exchange_params={
                'exchange': 'test_exchange',
                'exchange_type': 'direct',
                'passive': False,
                'durable': True,
                'auto_delete': False
            },
            routing_key='resp_key',
        )
    )

if __name__ == '__main__':
    main()
```