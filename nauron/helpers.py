import logging
import json
from io import BytesIO

from dataclasses import dataclass, asdict
from typing import Optional, Union, Dict

from flask.helpers import make_response, send_file
from flask import jsonify, abort

LOGGER = logging.getLogger(__name__)

SIZE_WARNING_THRESHOLD = 64
SIZE_ERROR_THRESHOLD = 128

@dataclass
class Response:
    """
    A dataclass that can be used to store HTTP responses and transfer it over the message queue if needed.
    """
    content: Optional[Union[bytes, str, Dict]] = None
    http_status_code: int = 200
    mimetype: str = 'application/json'

    def encode(self) -> bytes:
        if type(self.content) == bytes:
            self.content = self.content.decode('ISO-8859-1')
        return json.dumps(asdict(self)).encode("utf8")

    def flask_response(self):
        """
        Returns a Flask-friendly response or aborts the request if needed.
        """
        if self.http_status_code != 200:
            if self.content is None:
                abort(status=self.http_status_code)
            else:
                abort(status=self.http_status_code, description=self.content)

        if self.mimetype == 'application/json':
            return make_response(jsonify(self.content), self.http_status_code)
        else:
            if type(self.content) == str:
                self.content = self.content.encode('ISO-8859-1')
            return send_file(BytesIO(self.content), mimetype=self.mimetype)
