import logging
from typing import Dict
from random import randint

import pika
from marshmallow import Schema, fields, ValidationError

from nauron import Response, Worker

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("pika").setLevel(level=logging.WARNING)

logger = logging.getLogger('my_service')

class SampleSchema(Schema):
    """The required request schema for the service."""
    text = fields.Raw(validate=(lambda obj: type(obj) in [str, list]))

class SampleWorker(Worker):
    def __init__(self):
        self.schema = SampleSchema
        logger.info("Worker initialized.")

    def process_request(self, content: Dict, _:str) -> Response:
        try:
            content = self.schema().load(content)
        except ValidationError as error:
            return Response(content=error.messages, http_status_code=400)

        rnd = randint(0, 2)
        if rnd == 0:
            return Response({'Result:': "Response for text(s): {}".format(content['text'])})
        elif rnd == 1:
            return Response(content=b' ', mimetype="audio/wav")
        else:
            return Response(http_status_code=400,
                            content="There was a random issue with your request.")


if __name__ == "__main__":
    mq_parameters = pika.ConnectionParameters(host='localhost',
                                              port=5672,
                                              credentials=pika.credentials.PlainCredentials(username='guest',
                                                                                            password='guest'))
    worker = SampleWorker()
    worker.start(connection_parameters=mq_parameters, service_name='sample_service')
