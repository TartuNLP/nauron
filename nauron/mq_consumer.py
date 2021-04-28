import json
import logging
from sys import getsizeof
from time import time, sleep

from dataclasses import dataclass
from typing import Tuple, Optional, Dict

import pika
import pika.exceptions

from nauron import Worker
from nauron.helpers import Response, SIZE_WARNING_THRESHOLD, SIZE_ERROR_THRESHOLD

LOGGER = logging.getLogger(__name__)


@dataclass
class MQItem:
    """
    Parameters of a request sent via RabbitMQ.
    """
    delivery_tag: Optional[int]
    reply_to: Optional[str]
    correlation_id: Optional[str]
    request: Dict


class MQConsumer:
    def __init__(self, worker: Worker,
                 connection_parameters: pika.connection.ConnectionParameters, exchange_name: str,
                 routing_key: str = "default",
                 alt_routes: Tuple[str] = ()):
        """
        Initializes a RabbitMQ consumer class that listens for requests for a specific worker and responds to
        them.

        :param worker: A worker instance to be used.
        :param connection_parameters: RabbitMQ connection_parameters parameters.
        :param exchange_name: RabbitMQ exchange name.
        :param routing_key: RabbitMQ routing key. The actual queue name will also automatically include the service
        name to ensure that unique queues names are used.
        :param alt_routes: alternative allowed routing keys to be used in case of dynamic routing.
        """
        self.worker = worker

        self.exchange_name = exchange_name
        self.queue_name = '{}.{}'.format(exchange_name, routing_key)
        self.alt_routes = ['{}.{}'.format(exchange_name, alt_route) for alt_route in alt_routes]
        self.connection_parameters = connection_parameters
        self.channel = None

    def start(self):
        """
        Connect to RabbitMQ and start listening for requests. Automatically tries to reconnect if the connection
        is lost.
        """
        while True:
            try:
                self._connect()
                LOGGER.info('Ready to process requests.')
                self.channel.start_consuming()
            except pika.exceptions.AMQPConnectionError as e:
                LOGGER.error(e)
                LOGGER.info('Trying to reconnect in 10 seconds.')
                sleep(10)
            except KeyboardInterrupt:
                LOGGER.info('Interrupted by user. Exiting...')
                self.channel.close()
                break

    def _connect(self):
        """
        Connects to RabbitMQ, (re)declares the exchange for the service and a queue for the worker binding
        any alternative routing keys as needed.
        """
        LOGGER.info(f'Connecting to RabbitMQ server: {{host: {self.connection_parameters.host}, '
                    f'port :{self.connection_parameters.port}}}')
        connection = pika.BlockingConnection(self.connection_parameters)
        self.channel = connection.channel()
        self.channel.queue_declare(queue=self.queue_name)
        self.channel.exchange_declare(exchange=self.exchange_name, exchange_type='direct')
        self.channel.queue_bind(exchange=self.exchange_name, queue=self.queue_name, routing_key=self.queue_name)
        for alt_route in self.alt_routes:
            self.channel.queue_bind(exchange=self.exchange_name, queue=self.queue_name, routing_key=alt_route)

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue=self.queue_name, on_message_callback=self._on_request)

    @staticmethod
    def _respond(channel: pika.adapters.blocking_connection.BlockingChannel, mq_item: MQItem, response: bytes):
        """
        Publish the response to the callback queue and acknowlesge the original queue item.
        """
        channel.basic_publish(exchange='',
                              routing_key=mq_item.reply_to,
                              properties=pika.BasicProperties(correlation_id=mq_item.correlation_id),
                              body=response)
        channel.basic_ack(delivery_tag=mq_item.delivery_tag)

    def _on_request(self, channel: pika.adapters.blocking_connection.BlockingChannel, method: pika.spec.Basic.Deliver,
                    properties: pika.BasicProperties, body: bytes):
        """
        Pass the request to the worker and return its response.
        """
        t1 = time()
        mq_item = MQItem(method.delivery_tag,
                         properties.reply_to,
                         properties.correlation_id,
                         json.loads(body))
        LOGGER.info(f"Received request: {{id: {mq_item.correlation_id}, size: {getsizeof(body)} bytes}}")
        try:
            response = self.worker.process_request(mq_item.request['content'], mq_item.request['signature']).encode()
        except Exception as e:
            LOGGER.error(e)
            response = Response(http_status_code=500).encode()

        respose_size = getsizeof(response)
        if respose_size > 1024 * 1024 * SIZE_WARNING_THRESHOLD:
            LOGGER.warning(f"Response size exceeds the recommended threshold: {{id: {mq_item.correlation_id},"
                           f"size: {respose_size}}}")
        if respose_size > 1024 * 1024 * SIZE_ERROR_THRESHOLD:
            LOGGER.error(f"Response size exceeds RabbitMQ message size threshold: {{id: {mq_item.correlation_id},"
                           f"size: {respose_size}}}")
            response = Response(http_status_code=413).encode()

        self._respond(channel, mq_item, response)
        t2 = time()

        LOGGER.info(f"Request processed: {{id: {mq_item.correlation_id}, duration: {round(t2 - t1, 3)} s, "
                    f"size: {respose_size} bytes}}")
