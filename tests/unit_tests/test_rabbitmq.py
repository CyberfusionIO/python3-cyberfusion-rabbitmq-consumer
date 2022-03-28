import pika
import requests

from cyberfusion.RabbitMQConsumer.RabbitMQ import (
    RabbitMQ,
    get_config_file_path,
)


def test_config_file_path() -> None:
    """Test config file path."""
    assert get_config_file_path() == "/etc/cyberfusion/rabbitmq.yml"


def test_rabbitmq_config(rabbitmq: RabbitMQ) -> None:
    """Test attribute of RabbitMQ object."""
    assert rabbitmq.config == {
        "server": {
            "host": "rabbitmq",
            "username": "test",
            "password": "knvPSBPLkJSwTdMn6F4kkQkB",
            "port": 5672,
            "ssl": False,
        },
        "virtual_hosts": {
            "test": {
                "queue": "test",
                "exchanges": {"dx_service_reload": {"type": "direct"}},
            }
        },
    }


def test_rabbitmq_ssl_options(rabbitmq: RabbitMQ) -> None:
    """Test attribute of RabbitMQ object."""
    assert rabbitmq.ssl_options is None
    # TODO Check config with SSL, assert rabbitmq.ssl_options.server_hostname == 'rabbitmq'


def test_rabbitmq_connection(rabbitmq: RabbitMQ) -> None:
    """Test attribute of RabbitMQ object."""
    assert rabbitmq.connection.is_open


def test_rabbitmq_channel(rabbitmq: RabbitMQ) -> None:
    """Test attribute of RabbitMQ object."""
    assert rabbitmq.channel.connection == rabbitmq.connection


def test_rabbitmq_queue_declare(rabbitmq: RabbitMQ) -> None:
    """Test RabbitMQ declared queue."""
    queues = requests.get(
        "http://rabbitmq:15672/api/queues/test",
        auth=("test", "knvPSBPLkJSwTdMn6F4kkQkB"),
    ).json()

    assert any(
        queue["vhost"] == "test"
        and queue["name"] == "test"
        and queue["durable"]
        for queue in queues
    )


def test_rabbitmq_exchange_declare(rabbitmq: RabbitMQ) -> None:
    """Test RabbitMQ declared exchange."""
    exchanges = requests.get(
        "http://rabbitmq:15672/api/exchanges/test",
        auth=("test", "knvPSBPLkJSwTdMn6F4kkQkB"),
    ).json()

    assert any(
        exchange["vhost"] == "test"
        and exchange["name"] == "dx_service_reload"
        and exchange["type"] == "direct"
        for exchange in exchanges
    )


def test_rabbitmq_binding(rabbitmq: RabbitMQ) -> None:
    """Test RabbitMQ bound exchange to queue."""
    bindings = requests.get(
        "http://rabbitmq:15672/api/exchanges/test/dx_service_reload/bindings/source",
        auth=("test", "knvPSBPLkJSwTdMn6F4kkQkB"),
    ).json()

    assert any(
        binding["vhost"] == "test"
        and binding["source"] == "dx_service_reload"
        and binding["destination"] == "test"
        and binding["destination_type"] == "queue"
        for binding in bindings
    )
