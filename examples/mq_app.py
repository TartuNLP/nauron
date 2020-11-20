from flask_restful import Api
from flask import Flask
from flask_cors import CORS
import pika
import logging

from nauron import Sauron, MQSauronConf

# Define Flask application
app = Flask(__name__)
api = Api(app)
CORS(app)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s : %(message)s")
logging.getLogger("pika").setLevel(level=logging.WARNING)

mq_parameters = pika.ConnectionParameters(host='localhost',
                                          port=5672,
                                          credentials=pika.credentials.PlainCredentials(username='guest',
                                                                                        password='guest'))

conf = MQSauronConf(nazguls={'public': 'default'}, application_required=True,
                    connection_parameters=mq_parameters, exchange_name='randomservice')

# Define API endpoints
api.add_resource(Sauron, '/api/randomservice', resource_class_args=(conf, ))


if __name__ == '__main__':
    app.run()
