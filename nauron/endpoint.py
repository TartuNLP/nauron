import logging

from flask.views import MethodView
from flask import abort, request

from webargs import fields
from webargs.flaskparser import use_args

from nauron import ServiceConf
from nauron.mq_producer import MQProducer

LOGGER = logging.getLogger(__name__)


HEADERS = {
    "x-api-key": fields.Str(missing="public"),
    "application": fields.Str(missing=None)
}


class Endpoint(MethodView):
    """
    A MethodView that sends requests to the relevant service's worker directly or via RabbitMQ.
    """
    def __init__(self, conf: ServiceConf):
        self.conf = conf
        if self.conf.mq_connection_params:
            self._process_request = self._process_remotely
        else:
            self._process_request = self._process_locally

        self.request = {}

        self.engine = None
        self.response = None

    def _resolve_engine(self, headers):
        """
        Resolves the worker or engine configuration based on the api key in request header.
        """
        try:
            self.engine = self.conf.engines[headers['x-api-key']]
        except KeyError:
            abort(401, description="Invalid authentication token.")

    def _process_remotely(self):
        """
        Combines the routing key for the requests and forwards it to an MQProducer.
        """
        routing_key = '{}.{}'.format(self.conf.name, self.engine.name)
        for key in self.engine.routing_pattern:
            try:
                routing_key+= '.{}'.format(self.request['body'][key])
            except KeyError:
                abort(400, description='Mandatory parameter {} missing'.format(key))

        producer = MQProducer(self.conf.mq_connection_params, self.conf.name)
        self.response = producer.publish_request(self.request,
                                                 routing_key=routing_key,
                                                 message_timeout=self.conf.timeout)

    def _process_locally(self):
        """
        Forwards the request directly to a local engine.
        """
        self.response = self.engine.process_request(self.request['body'], self.request['application'])

    @use_args(HEADERS, location="headers")
    def post(self, headers):
        """
        Processes the POST request locally or via RabbitMQ.
        """
        self._resolve_engine(headers)
        self.request['body'] = request.get_json()
        self.request['application'] = headers['application']

        self._process_request()

        return self.response.rest_response()

    @use_args(HEADERS, location="headers")
    def get(self, headers):
        """
        Returns a static GET request response if defined in engine configuration.
        TODO currently not compatible with local deployment.
        """
        self._resolve_engine(headers)
        if self.engine.config_info:
            return self.engine.config_info
        else:
            abort(405)
