from polyfactory.factories.pydantic_factory import ModelFactory

from cyberfusion.RabbitMQConsumer.config import Config

from cyberfusion.RPCClient import RabbitMQCredentials, RPCClient

from cyberfusion.RabbitMQConsumer.contracts import HandlerBase
from cyberfusion.RabbitMQConsumer.utilities import (
    get_exchange_handler_class_request_model,
    import_exchange_handler_modules,
)

config = Config("rabbitmq.yml")

assert len(config.virtual_hosts) == 1

virtual_host = config.virtual_hosts[0]

assert len(virtual_host.exchanges) == 1

exchange = virtual_host.exchanges[0]

credentials = RabbitMQCredentials(
    ssl_enabled=config.server.ssl,
    port=config.server.port,
    host=config.server.host,
    username=config.server.username,
    password=config.server.password,
    virtual_host_name=virtual_host.name,
)

client = RPCClient(
    credentials,
    queue_name=virtual_host.queue,
    exchange_name=exchange.name,
    timeout=5,
)


def get_handler() -> HandlerBase:
    modules = import_exchange_handler_modules([exchange])

    module = modules[exchange.name]

    handler = module.Handler()

    return handler


def get_body(handler: HandlerBase) -> dict:
    request_model = get_exchange_handler_class_request_model(handler)

    factory = ModelFactory.create_factory(request_model)

    built_model = factory.build()

    body = built_model.dict()

    return body


handler = get_handler()

body = get_body(handler)

response = client.request(body)

print(response)
