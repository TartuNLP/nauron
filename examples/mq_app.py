from flask import Flask
from flask_cors import CORS
import pika
import logging

from nauron import Endpoint, ServiceConf, EngineConf

# Define Flask application
app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("pika").setLevel(level=logging.WARNING)

mq_parameters = pika.ConnectionParameters(host='localhost',
                                          port=5672,
                                          credentials=pika.credentials.PlainCredentials(username='guest',
                                                                                        password='guest'))

service_conf = ServiceConf(name='randomservice',
                           endpoint='/api/randomservice',
                           mq_connection_params=mq_parameters,
                           engines={'public':EngineConf()})

# Define API endpoints
app.add_url_rule(service_conf.endpoint, view_func=Endpoint.as_view(service_conf.name, service_conf))


if __name__ == '__main__':
    app.run()
