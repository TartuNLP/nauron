import logging
from typing import Dict, Any
from random import randint

import pika

from nauron import Response, Nazgul, MQConsumer

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(name)s : %(message)s")
logging.getLogger("pika").setLevel(level=logging.WARNING)

logger = logging.getLogger('mynazgul')


class RandomNazgul(Nazgul):
    def __init__(self):
        logger.info("Loading imaginary model...")

    def process_request(self, request: Dict[str, Any]) -> Response:
        rnd = randint(0, 2)
        if rnd == 0:
            return Response({'Result:': "Response for string: {}".format(request['text'])})
        elif rnd == 1:
            return Response(content=b' ', mimetype="audio/wav")
        else:
            return Response(http_status_code=400,
                            content="We randomly decided that we could not process your request.")


if __name__ == "__main__":
    mq_parameters = pika.ConnectionParameters(host='localhost',
                                              port=5672,
                                              credentials=pika.credentials.PlainCredentials(username='guest',
                                                                                            password='guest'))

    service = MQConsumer(RandomNazgul(), mq_parameters, 'randomservice', queue_name='default')
    service.start()
