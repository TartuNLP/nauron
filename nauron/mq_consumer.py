import json
import logging
from time import time, sleep

from dataclasses import dataclass
from typing import Optional, Any, Dict, Tuple

import pika
import pika.exceptions

from nauron import Nazgul
from nauron.response import Response

LOGGER = logging.getLogger(__name__)


@dataclass
class MQItem:
    """
    Parameters of a request sent via RabbitMQ.
    """
    delivery_tag: Optional[int]
    reply_to: Optional[str]
    correlation_id: Optional[str]
    request: Dict[str, Any]


class MQConsumer:
    def __init__(self, nazgul: Nazgul,
                 connection_parameters: pika.connection.ConnectionParameters, exchange_name: str,
                 nazgul_name: str = "public",
                 alt_routes: Tuple[str] = ()):
        """
        Initializes a RabbitMQ consumer class that listens for requests for a specific Nazgul instance and responds to
        them.
        :param nazgul: A Nazgul instance to be used.
        :param connection_parameters: RabbitMQ host and user parameters.
        :param exchange_name: the name used in the ServiceConf instance in the API implementation.
        :param nazgul_name: the name used in NazgulConf defined in the API implementation, or if dynamic routing keys
        are used, their allowed values should be included (separated with dots), for example 'public.et.en'
        :param alt_routes: alternative allowed routing keys to be used in case of dynamic routing, for example in
        addition to 'public.et.en', 'public.est.eng' might be allowed if routing is based on language codes.
        """
        self.nazgul = nazgul

        self.exchange_name = exchange_name
        self.queue_name = '{}.{}'.format(exchange_name, nazgul_name)
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
                LOGGER.info('Trying to reconnect in 30 seconds.')
                sleep(30)
            except KeyboardInterrupt:
                LOGGER.info('Interrupted by user. Exiting...')
                self.channel.close()
                break


    def _connect(self):
        """
        Connects to RabbitMQ, (re)declares the service exchange and a queue for the Nazgul configuration binding
        any alternative routing keys as needed.
        """
        LOGGER.info('Connecting to RabbitMQ server {}:{}.'.format(self.connection_parameters.host,
                                                                  self.connection_parameters.port))
        connection = pika.BlockingConnection(self.connection_parameters)
        self.channel = connection.channel()
        self.channel.queue_declare(queue=self.queue_name)
        self.channel.exchange_declare(exchange=self.exchange_name, exchange_type='direct')
        self.channel.queue_bind(exchange=self.exchange_name, queue=self.queue_name, routing_key=self.queue_name)
        for alt_route in self.alt_routes:
            self.channel.queue_bind(exchange=self.exchange_name, queue=self.queue_name, routing_key=alt_route)

        # Start listening on channel with prefetch_count=1
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue=self.queue_name, on_message_callback=self._on_request)

    @staticmethod
    def _respond(channel: pika.adapters.blocking_connection.BlockingChannel, mq_item: MQItem, response: Response):
        """
        Publish the response to the callback queue and acknowlesge the original queue item.
        """
        channel.basic_publish(exchange='',
                              routing_key=mq_item.reply_to,
                              properties=pika.BasicProperties(correlation_id=mq_item.correlation_id),
                              body=response.encode())
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

        LOGGER.debug(f"Request: {mq_item.request}")
        response = self.nazgul.process_request(mq_item.request['body'], mq_item.request['application'])
        LOGGER.debug(f"Response: {response}")
        self._respond(channel, mq_item, response)
        t4 = time()

        LOGGER.debug(f"On_request took: {round(t4 - t1, 3)} s. ")