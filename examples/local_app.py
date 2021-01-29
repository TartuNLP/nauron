from flask import Flask
from flask_cors import CORS

from nauron import Sauron, ServiceConf
from random_nazgul.random_nazgul import RandomNazgul

# Define Flask application
app = Flask(__name__)
CORS(app)

service_conf = ServiceConf(name='randomservice',
                           endpoint='/api/randomservice',
                           nazguls={'public': RandomNazgul()})


# Define API endpoints
app.add_url_rule(service_conf.endpoint, view_func=Sauron.as_view(service_conf.name, service_conf))


if __name__ == '__main__':
    app.run()
