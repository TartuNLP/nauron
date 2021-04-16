# Nauron

Nauron is a Flask wrapper for Python designed to enable simple creation of distributed API services.
 By default, the services communicate via a RabbitMQ message broker and was designed with neural networks in mind to
 keep GPU-accelerated processes separate from the API logic. The API gateway is responsible for some request
  preprocesing, verification and routing, as well as serving any static
 endpoints.

New services can be added by implementing the Service class and creating an Endpoint instance