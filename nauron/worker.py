import logging
from abc import abstractmethod

from typing import Tuple, Dict

from nauron.helpers import Response

LOGGER = logging.getLogger(__name__)


class Worker:
    _consumer = None
    """
    An abstract service logic class that responds to Sauron requests directly or via RabbitMQ.
    """

    @abstractmethod
    def process_request(self, content: Dict, signature: str) -> Response:
        """
        Method for processing the request. Request verification should also be done as this will be the first time the
        request body is processed (unless dynamic routing parameters are looked up).

        :param content: A dict representing the content of the request.
        :param signature: Optional value that can be used to map the request to a specific function. Can be useful,
        when the same service is used by multiple slightly different endpoints.
        """
        pass

    def start(self, connection_parameters, service_name: str,
              routing_key: str = "default", alt_routes: Tuple[str] = ()):
        """
        Starts a RabbitMQ consumer that listens for requests.

        :param connection_parameters: RabbitMQ host and user parameters.
        :param service_name: Nauron service name. Used by RabbitMQ as the exchange name. Should be identical to the
        name parameter in Service.
        :param routing_key: Worker's routing key. Will be used by RabbitMQ as the queue name. The actual queue name
        will also  automatically include the service name to ensure that unique queues names are used.
        :param alt_routes: alternative allowed routing keys to be used in case of dynamic routing, for example in
        addition to 'default.et.en', 'default.est.eng' might be allowed if routing is based on language codes.
        """
        from nauron.mq_consumer import MQConsumer
        self._consumer = MQConsumer(worker=self,
                                    connection_parameters=connection_parameters,
                                    exchange_name=service_name,
                                    routing_key=routing_key,
                                    alt_routes=alt_routes)

        self._consumer.start()
