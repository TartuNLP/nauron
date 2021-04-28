import uuid
from time import sleep, time
import logging
from typing import Dict, Optional
from dataclasses import dataclass, field

import pika
import pika.exceptions
from flask import Flask

from nauron.worker import Worker

LOGGER = logging.getLogger(__name__)


@dataclass
class Service:
    name: str
    timeout: int
    remote: bool = False
    mq_parameters: Optional[pika.ConnectionParameters] = None
    workers: Dict[str, Worker] = field(default_factory=dict)

    def __post_init__(self):
        if self.remote:
            while True:
                try:
                    connection = pika.BlockingConnection(self.mq_parameters)
                    channel = connection.channel()
                    channel.exchange_declare(exchange=self.name, exchange_type='direct')
                    channel.close()
                    connection.close()
                    LOGGER.info(f'MQ exchange for service {self.name} initialized.')
                    break
                except pika.exceptions.AMQPConnectionError as e:
                    LOGGER.error(e)
                    LOGGER.error(f"Unable to initialize MQ exchange for service {self.name}.")
                    LOGGER.info('Trying to reconnect in 10 seconds.')
                    sleep(10)

    def add_worker(self,
                   worker: Worker,
                   routing_key: str = "default"):
        """
        Adds a local worker instance to the service.
        :param worker: A nauron Worker instance.
        :param routing_key: An optional routing key that can be used to map any request to this worker. Useful when
        multiple unique workers exist for the service. In case the same routing key is used multiple times,
        the last mapping will be used.
        """
        self.workers[routing_key]=worker

    def process_request(self,
                        content: Dict,
                        signature: str = "default",
                        routing_key: str = "default"):
        """
        Processes the request either with a local worker or remotely via RabbitMQ. Maps to the process_request() method
        of the equivalent worker.

        :param content: A dict representing the content of the request.
        :param signature: Optional value that can be used to map the request to a specific function. Can be useful,
        when the same service is used by multiple slightly different endpoints.
        :param routing_key: An optional value to map the request to a specific worker. For remote workers this will
        be used to form the queue name. In case service uses a mix of remote and local workers, the local worker
        mapping is prioritized.
        :return: Returns a Flask-friendly response from nauron's Response object.
        """
        if self.remote and routing_key not in self.workers:
            from nauron.mq_producer import MQProducer
            producer = MQProducer(self.mq_parameters, self.name)
            response = producer.publish_request(
                {"signature": signature, "content": content},
                routing_key='{}.{}'.format(self.name, routing_key),
                message_timeout=self.timeout)
        else:
            correlation_id = str(uuid.uuid4())
            LOGGER.info(f"Forwarding request to local worker: {{id: {correlation_id}, worker: {routing_key}}}")
            t1 = time()
            response = self.workers[routing_key].process_request(content, signature)
            t2 = time()
            LOGGER.info(f"Request processed: {{id: {correlation_id}, duration: {round(t2 - t1, 3)}}}")

        return response.flask_response()

class Nauron(Flask):
    _services: Dict[str, Service] = {}
    """
    A Flask wrapper that stores the default timeout value for the message queue and provides basic decorations for
    routing.
    """

    def __init__(self, import_name,
                 timeout: int = 60000,
                 mq_parameters: Optional[pika.ConnectionParameters] = None,
                 **kwargs):
        """
        :param import_name: Flask import_name
        :param timeout: Default timeout value for the message queue
        :param mq_parameters: RabbitMQ connection parameters required for remote services.
        :param kwargs: additional Flask parameters
        """
        self._timeout = timeout
        self._mq_parameters = mq_parameters
        super().__init__(import_name, **kwargs)

    def add_service(self,
                    name: str,
                    remote: bool = False) -> Service:
        """"
        Adds a new service that is used to process requests by local or remote workers.

        :param name: Name of the service, in case of a remote service, the same name must be used when initializing
        the consumer.
        :param remote: A boolean value that defines whether the service has any remote workers. Enabling this will
        still allow for adding local workers to the service.
        """
        service = Service(name=name, remote=remote, mq_parameters=self._mq_parameters,
                                                 timeout=self._timeout)
        self._services[name] = service
        return service

    def add_worker(self,
                   service_name: str,
                   worker: Worker,
                   routing_key: str = "default"):
        """
        Adds a local worker instance to the service.

        :param service_name: Name of the service. If the service does not exist, a new one will be created
        automatically.
        :param worker: A nauron Worker instance.
        :param routing_key: An optional routing key that can be used to map any request to this worker. Useful when
        multiple unique workers exist for the service. In case the same routing key is used multiple times,
        the last mapping will be used.
        """
        if service_name not in self._services:
            self.add_service(name=service_name)
        self._services[service_name].add_worker(worker, routing_key)

    def process_request(self, service_name: str, *args, **kwargs):
        """
        Process request by its service name. Equivalent of Worker.process_request(*args, **kwargs).
        """
        self._services[service_name].process_request(*args, **kwargs)

    def _route(self, method: str, rule, **options):
        def decorator(view_func):
            endpoint = options.pop("endpoint", None)
            options.pop("methods", None)
            self.add_url_rule(rule, endpoint, view_func, methods=[method], **options)
            return view_func

        return decorator

    def get(self, rule, **options):
        """
        A GET request decorator where this:
            @app.get(rule, **options)
        is equivalent to Flask's:
            @app.route('/', methods=["GET"])
        """
        return self._route("GET", rule, **options)

    def post(self, rule, **options):
        """
        A POST request decorator where this:
            @app.get(rule, **options)
        is equivalent to Flask's:
            @app.route('/', methods=["POST"])
        """
        return self._route("POST", rule, **options)

    def put(self, rule, **options):
        """
        A PUT request decorator where this:
            @app.get(rule, **options)
        is equivalent to Flask's:
            @app.route('/', methods=["PUT"])
        """
        return self._route("PUT", rule, **options)

    def delete(self, rule, **options):
        """
        A DELETE request decorator where this:
            @app.get(rule, **options)
        is equivalent to Flask's:
            @app.route('/', methods=["DELETE"])
        """
        return self._route("DELETE", rule, **options)

    def head(self, rule, **options):
        """
        A HEAD request decorator where this:
            @app.get(rule, **options)
        is equivalent to Flask's:
            @app.route('/', methods=["HEAD"])
        """
        return self._route("HEAD", rule, **options)
