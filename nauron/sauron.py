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


class Sauron(MethodView):
    """
    A MethodView that sends requests to the relevant worker directly or via RabbitMQ.
    """
    def __init__(self, conf: ServiceConf):
        self.conf = conf
        if self.conf.mq_connection_params:
            self.process = self._mq_process
        else:
            self.process = self._local_process

        self.request = {}

        self.nazgul = None
        self.response = None

    def _resolve_nazgul(self, headers):
        """
        Resolves Nazgul instance or its configuration based on the api key in request header.
        """
        try:
            self.nazgul = self.conf.nazguls[headers['x-api-key']]
        except KeyError:
            abort(401, description="Invalid authentication token.")

    def _mq_process(self):
        """
        Combines the routing key for the requests and forwards it to an MQProducer.
        """
        routing_key = '{}.{}'.format(self.conf.name, self.nazgul.name)
        for key in self.nazgul.routing_pattern:
            try:
                routing_key+= '.{}'.format(self.request['body'][key])
            except KeyError:
                abort(400, description='Mandatory parameter {} missing'.format(key))

        producer = MQProducer(self.conf.mq_connection_params, self.conf.name)
        self.response = producer.publish_request(self.request,
                                                 routing_key=routing_key,
                                                 message_timeout=self.conf.timeout)

    def _local_process(self):
        """
        Forwards the request to a Nazgul instance.
        """
        self.response = self.nazgul.process_request(self.request['body'], self.request['application'])

    @use_args(HEADERS, location="headers")
    def post(self, headers):
        """
        Processes the POST request locally or via RabbitMQ.
        """
        self._resolve_nazgul(headers)
        self.request['body'] = request.get_json()
        self.request['application'] = headers['application']

        self.process()

        return self.response.rest_response()

    @use_args(HEADERS, location="headers")
    def get(self, headers):
        """
        Returns a static GET request response if defined in Nazgul configuration.
        TODO currently not compatible with local deployment.
        """
        self._resolve_nazgul(headers)
        if self.nazgul.config_info:
            return self.nazgul.config_info
        else:
            abort(405)
