from flask import request
from flask_cors import CORS

from nauron import Nauron

from sample_service.sample_service import SampleWorker

# Define application
app = Nauron(__name__)
CORS(app)

app.add_worker(service_name='sample_service', worker=SampleWorker())


@app.post('/sample-service')
def randomservice():
    response = app.process_request(service_name='sample_service', content=request.json)
    return response


if __name__ == '__main__':
    app.run()
