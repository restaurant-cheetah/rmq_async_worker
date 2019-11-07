import pika

import abc

class ResponseHandler(abc.ABC):
    @abc.abstractmethod
    def response(self):
        pass

class RmqResponseHandler:
    def __init__(
            self,
            connection_parameters: pika.ConnectionParameters = pika.ConnectionParameters(),
            exchange_params={},
            routing_key='',
            publish_properties=pika.BasicProperties(content_type='application/octet-stream', delivery_mode=2)
    ):
        self._connection_parameters = connection_parameters
        self._exchange_params = exchange_params
        self._routing_key = routing_key
        self._publish_properties = publish_properties

    def response(self, message: bytes):
        connection = pika.BlockingConnection(self._connection_parameters)
        channel = connection.channel()
        channel.exchange_declare(**self._exchange_params)
        channel.basic_publish(
            self._exchange_params['exchange'],
            self._routing_key,
            message,
            self._publish_properties
        )
        connection.close()
