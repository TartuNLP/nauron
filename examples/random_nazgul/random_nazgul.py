import logging
from typing import Dict, Any
from random import randint

import pika
from marshmallow import Schema, fields, ValidationError

from nauron import Response, Nazgul, MQConsumer

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("pika").setLevel(level=logging.WARNING)

logger = logging.getLogger('mynazgul')

class RandomSchema(Schema):
    """The required schema for this imaginary service."""
    text = fields.Raw(validate=(lambda obj: type(obj) in [str, list]))

class RandomNazgul(Nazgul):
    def __init__(self, request_schema: Schema() = RandomSchema):
        self.schema = request_schema
        logger.info("Loading imaginary model...")

    def process_request(self, body: Dict[str, Any], _:str = None) -> Response:
        # Checks and the request format matches our schema.
        try:
            body = self.schema().load(body)
        except ValidationError as error:
            return Response(content=error.messages, http_status_code=400)

        rnd = randint(0, 2)
        if rnd == 0:
            return Response({'Result:': "Response for text(s): {}".format(body['text'])})
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

    service = MQConsumer(nazgul=RandomNazgul(RandomSchema),
                         connection_parameters=mq_parameters,
                         exchange_name='randomservice')
    service.start()
