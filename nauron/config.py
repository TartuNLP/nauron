import logging

from dataclasses import dataclass
from typing import Dict, Union, Optional, Tuple

import pika
import pika.exceptions

from nauron import Nazgul

LOGGER = logging.getLogger(__name__)


@dataclass
class NazgulConf:
    """
    Configuration for a RabbitMQ-based worker.

    :param name (str): worker name that is combined with the service name to create a unique routing key.
    :param routing_pattern_keys (tuple): a set of keys for values to be looked up from the request body to be used as
    additional dynamic routing keys
    :param config_info (str/dict): static content to be returned upon a GET request. Common usage would be for some
    machine-readable configuration info to automatically expose a list of supported parameters.
    """
    name: str = 'public'
    routing_pattern: [Tuple[str]] = ()
    config_info: Optional[Union[Dict, str]] = None


@dataclass()
class ServiceConf:
    """
    Configuration for a single service / endpoint.

    :param name (str): Name or the flask view, rabbitmq exchange (if applicable) and an element of the routing key.
    :param endpoint (str):
    :param timeout (int): RabbitMQ message timeout in milliseconds. Should be equal to the API request timeout.
    :param nazguls (dict): A mapping of authentication tokens (default: 'public') to nazgul instances or NazgulConfig
    instances referring to RabbitMQ-based workers.
    """
    name: str
    endpoint: str
    timeout: int = 60000
    mq_connection_params: Optional[pika.connection.ConnectionParameters] = None
    nazguls: Optional[Dict[str, Union[NazgulConf, Nazgul]]] = None

    def __post_init__(self):
        """
        Initialize RabbitMQ exchanges.
        """
        if self.mq_connection_params:
            connection = pika.BlockingConnection(self.mq_connection_params)
            channel = connection.channel()
            channel.exchange_declare(exchange=self.name, exchange_type='direct')
            channel.close()
            connection.close()
