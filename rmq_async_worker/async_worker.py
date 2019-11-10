import pika
import threading
import functools
import logging

from enum import Enum


class AckMode(Enum):
    ON_RECEIVED = 1
    ON_RESPOND = 2


class AsyncWorker:
    def __init__(
            self,
            connection_parameters: pika.ConnectionParameters = pika.ConnectionParameters(),
            exchange_params: dict = {},
            queue_params: dict = {},
            routing_key: str = '',
            prefetch_count: int = 1,
            logger: logging.Logger = logging.getLogger(__name__),
            ack_mode: AckMode = AckMode.ON_RECEIVED
    ):
        self.threads = []
        self.connection_parameters = connection_parameters
        self.connection = pika.BlockingConnection(parameters=connection_parameters)
        self.exchange_params = exchange_params
        self.queue_params = queue_params
        self.routing_key = routing_key
        self.prefetch_count = prefetch_count
        self.logger = logger
        self.ack_mode = ack_mode
        self.channel = None

    def start(self, worker, response_handler):
        ################################################################################################################
        # => Configuring exchanges and channels
        ################################################################################################################

        self.channel = channel = self.connection.channel()
        channel.exchange_declare(**self.exchange_params)
        channel.queue_declare(**self.queue_params)
        channel.queue_bind(
            queue=self.queue_params['queue'],
            exchange=self.exchange_params['exchange'],
            routing_key=self.routing_key
        )
        channel.basic_qos(prefetch_count=self.prefetch_count)

        ################################################################################################################
        # <= Configuring exchanges and channels
        ################################################################################################################

        self.logger.debug(
            'AsyncWorker is starting to work. '
            'Expecting messages from queue {}, bind to exchange {} with {} routing key. '
            'Prefetch count: {}. Ack mode: {}'.format(
                self.queue_params["queue"],
                self.exchange_params["exchange"],
                self.routing_key,
                self.prefetch_count,
                self.ack_mode
            ))

        on_message_callback = functools.partial(
            AsyncWorker.__on_message,
            args=(self, worker, response_handler)
        )
        channel.basic_consume(self.queue_params['queue'], on_message_callback)

        # Starting the consumption loop:
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            # Exiting with keyboard interruption
            channel.stop_consuming()
        except SystemExit:
            # Exiting upon getting system stop commands
            channel.stop_consuming()

        for thread in self.threads:
            thread.join()

        self.connection.close()

    @staticmethod
    def __on_message(channel, method_frame, props, body, args):
        logging.debug(
            "Message received: {} from channel: {}. "
            "With method_frame: {}. "
            "Receiving props: {}. ".format(
                body,
                channel,
                method_frame,
                props
            )
        )
        (async_worker, worker, response_handler) = args
        connection = async_worker.connection
        threads = async_worker.threads
        ack_mode = async_worker.ack_mode
        delivery_tag = method_frame.delivery_tag
        t = threading.Thread(
            target=AsyncWorker.__do_work,
            args=(connection, channel, props, delivery_tag, body, ack_mode, worker, response_handler)
        )
        t.start()
        threads.append(t)

    @staticmethod
    def __do_work(connection, channel, props, delivery_tag, body, ack_mode, worker, response_handler):
        try:
            ack_callback = functools.partial(AsyncWorker.__ack, channel, delivery_tag)
            if ack_mode == AckMode.ON_RECEIVED:
                connection.add_callback_threadsafe(ack_callback)
                results = worker.perform(body)
                response_handler.response(results, props)
            else:
                results = worker.perform(body)
                response_handler.response(results, props)
                connection.add_callback_threadsafe(ack_callback)
        except Exception as e:
            try:
                if ack_mode == AckMode.ON_RECEIVED:
                    pass
                else:
                    nack_callback = functools.partial(AsyncWorker.__nack, channel, delivery_tag)
                    connection.add_callback_threadsafe(nack_callback)
            except:
                pass

    @staticmethod
    def __ack(channel, delivery_tag):
        if channel.is_open:
            channel.basic_ack(delivery_tag=delivery_tag)
        else:
            pass

    @staticmethod
    def __nack(channel, delivery_tag):
        if channel.is_open:
            channel.basic_nack(delivery_tag)
        else:
            pass
