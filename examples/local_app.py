from flask_restful import Api
from flask import Flask
from flask_cors import CORS

from nauron import Sauron, LocalSauronConf
from random_nazgul.random_nazgul import RandomNazgul

# Define Flask application
app = Flask(__name__)
api = Api(app)
CORS(app)


conf = LocalSauronConf(nazguls={'public': RandomNazgul()}, application_required=False)


# Define API endpoints
api.add_resource(Sauron, '/api/randomservice', resource_class_args=(conf, ))


if __name__ == '__main__':
    app.run()
