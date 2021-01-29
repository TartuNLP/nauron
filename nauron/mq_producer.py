import json
import uuid
import logging

from typing import Any, Dict

from flask import abort
import pika
import pika.exceptions

from nauron.response import Response

LOGGER = logging.getLogger(__name__)


class MQProducer:
    def __init__(self, connection_parameters: pika.connection.Parameters, exchange_name: str):
        """
        Initializes a RabbitMQ producer class used for publishing requests using the relevant routing key and
        waits for the response.
        """
        self.response = None
        self.correlation_id = None
        self.callback_queue = None
        self.exchange_name = exchange_name

        try:
            self.mq_connection = pika.BlockingConnection(connection_parameters)
            self.channel = self.mq_connection.channel()
        except Exception as e:
            LOGGER.error(e)
            abort(503)

    def _init_callback(self):
        """
        Create an exclusive callback queue for the response.
        """
        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue
        self.channel.basic_consume(queue=self.callback_queue, on_message_callback=self._on_response, auto_ack=True)

    def _on_response(self, _, __, properties: pika.spec.BasicProperties, body: bytes):
        """
        Verifies that the correct response was sent and loads the it into a Response instance.
        """
        if properties.correlation_id == self.correlation_id:
            self.response = Response(**json.loads(body))

    def publish_request(self, request: Dict[str, Any], routing_key: str, message_timeout: int) -> Response:
        """
        Publishes the request to RabbitMQ, if no queue bound with the used routing key exists,
        the request is aborted with HTTP error 503.
        """
        self.channel.confirm_delivery()
        self._init_callback()
        self.correlation_id = str(uuid.uuid4())
        try:
            self.channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=routing_key,
                properties=pika.BasicProperties(
                    reply_to=self.callback_queue,
                    correlation_id=self.correlation_id,
                    expiration=str(message_timeout)),
                mandatory=True,
                body=json.dumps(request).encode()
            )
            while not self.response:
                self.mq_connection.process_data_events()

            self.channel.close()
            self.mq_connection.close()
            return self.response

        except pika.exceptions.UnroutableError:
            self.channel.close()
            self.mq_connection.close()
            return Response("Request cannot be processed. Check your request or try again later.",
                            http_status_code=503)
