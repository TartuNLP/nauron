# Nauron

Nauron is a Flask wrapper for Python designed to enable simple creation of distributed services. It was designed
 with AI applications in mind to keep GPU-accelerated or otherwise resource-intensive functionality separate from the
  API logic. 

A Nauron-based API may have multiple services configured to it. Each service has one or more workers. The local
 workers are simply instances of a Worker class. Remote workers are used when the communication with a Worker
  class instance is done via a RabbitMQ message broker. When multiple identical instances are connected to the
   message queue, the workload is automatically distributed between them.

A detailed documentation of Nauron is coming soon.