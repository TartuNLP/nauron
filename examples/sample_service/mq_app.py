from flask import request
from flask_cors import CORS
import pika

from nauron import Nauron

mq_parameters = pika.ConnectionParameters(host='localhost',
                                          port=5672,
                                          credentials=pika.credentials.PlainCredentials(username='guest',
                                                                                        password='guest'))

# Define application
app = Nauron(__name__, mq_parameters=mq_parameters)
CORS(app)

app.add_service(name='sample_service', remote=True)


@app.post('/sample-service')
def randomservice():
    response = app.process_request(service_name='sample_service', content=request.json)
    return response


if __name__ == '__main__':
    app.run()
