from .response_handler import ResponseHandler
import pika
import copy
import logging


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

    def response(self, message: bytes, request_props: pika.BasicProperties):
        publish_props = copy.copy(self._publish_properties)

        # Inserting correlation_id inside response
        if request_props.correlation_id:
            publish_props.correlation_id = request_props.correlation_id

        routing_key = self._routing_key

        # Overriding routing key, if it's defined inside request
        if request_props.reply_to:
            routing_key = request_props.reply_to

        connection = pika.BlockingConnection(self._connection_parameters)
        channel = connection.channel()
        channel.exchange_declare(**self._exchange_params)

        logging.info("Sending response: {}, to exchange: {} with {} routing_key.".format(
            message,
            self._exchange_params["exchange"],
            routing_key
        ))

        channel.basic_publish(
            self._exchange_params['exchange'],
            routing_key,
            message,
            publish_props
        )
        connection.close()
