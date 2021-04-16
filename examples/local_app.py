from flask import Flask
from flask_cors import CORS

from nauron import Endpoint, ServiceConf
from random_service.random_service import RandomService

# Define Flask application
app = Flask(__name__)
CORS(app)

service_conf = ServiceConf(name='randomservice',
                           endpoint='/api/randomservice',
                           engines={'public': RandomService()})


# Define API endpoints
app.add_url_rule(service_conf.endpoint, view_func=Endpoint.as_view(service_conf.name, service_conf))


if __name__ == '__main__':
    app.run()
