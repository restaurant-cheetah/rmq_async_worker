# rmq_async_worker

Package provides abstractions to create RabbitMQ async worker microservices.

## AsyncWorker

`AsyncWorker` provides general working module, that should be used as entry point for the entire application.
It's responsibility is to initialize RabbitMQ consuming connection and run the incoming event's loop.

In order to use it, the worker should be:

1. Initialized:
    ```python
    worker = AsyncWorker(**initialization_params)
    ```

1. Started:
    ```pyython
    worker.start(worker, handler)
    ```

### Parameters

* `connection_parameters` - any available `pika`'s [connection parameters](https://pika.readthedocs.io/en/stable/modules/parameters.html) in order to connect to RabbitMQ
* `exchange_params` - dict {str: str}, which keys and values are available to be used inside `pika`'s [exchange_declare](https://pika.readthedocs.io/en/stable/modules/channel.html#pika.channel.Channel.exchange_declare) method call
* `queue_params` - dict {str: str}, which keys and values are available to be used inside `pika`'s [queue_devlare](https://pika.readthedocs.io/en/stable/modules/channel.html#pika.channel.Channel.queue_declare)
* `routing_key` - string to be used as routing key to bind **queue** to **exchange**
* `prefetch_count` - integer, defines prefetch_count for established connection.
* `ack_mode` - one from the `AckMode` enum. Can be acked before request is got, or after result is sent.

## Worker

`Worker` should be specified as a static class - with `@classmethod` perform with next signature:

```haskell
preform :: (cls, msg: bytes) -> bytes
```

Worker can perform task in syncronos manner with thread blokings, because for each worker's `perform` call
new thread will be started.

## Response Handler

Abstract class, that defines the contract should be implemented for each concrete realization of the response handler.

## RmqResponseHandler

Concrete realization for the response handler - that sends responses back to RabbitMQ.

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