import logging
from abc import ABC, abstractmethod

from typing import Any, Dict, Optional

from nauron.response import Response

LOGGER = logging.getLogger(__name__)


class Service(ABC):
    """
    An abstract service logic class that responds to Sauron requests directly or via RabbitMQ.
    """
    @abstractmethod
    def process_request(self, body: Dict[str, Any], application: Optional[str] = None) -> Response:
        """
        Method for processing the request. Request verification should also be done as this will be the first time the
        request body is processed (unless dynamic routing parameters are looked up).

        :param body: A dict representing the original JSON body of the request.
        :param application: Optional request header value that is generally used for tracking request statistics,
        but could also be considered when different processing is used depending on the source of the request.
        """
        pass
