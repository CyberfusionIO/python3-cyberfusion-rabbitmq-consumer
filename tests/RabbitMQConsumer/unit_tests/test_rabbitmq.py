import os
from typing import Generator

import pika
import requests
from pytest_mock import MockerFixture  # type: ignore[attr-defined]

from cyberfusion.RabbitMQConsumer.RabbitMQ import (
    RabbitMQ,
    get_config_file_path,
)


def test_config_file_path(
    mocker: MockerFixture, rabbitmq: Generator[RabbitMQ, None, None]
) -> None:
    """Test config file path."""
    mocker.patch.dict(
        os.environ, {"RABBITMQ_CONSUMER_CONFIG_FILE_PATH": "test.yml"}
    )

    assert get_config_file_path() == "test.yml"


def test_rabbitmq_config(
    rabbitmq_virtual_host_name: str,
    rabbitmq_host: str,
    rabbitmq_amqp_port: int,
    rabbitmq_ssl: bool,
    rabbitmq_username: str,
    rabbitmq_password: str,
    rabbitmq_exchange_name: str,
    rabbitmq_queue_name: str,
    rabbitmq: Generator[RabbitMQ, None, None],
) -> None:
    assert rabbitmq.config == {
        "server": {
            "host": rabbitmq_host,
            "username": rabbitmq_username,
            "password": rabbitmq_password,
            "port": rabbitmq_amqp_port,
            "ssl": rabbitmq_ssl,
        },
        "virtual_hosts": {
            rabbitmq_virtual_host_name: {
                "queue": rabbitmq_queue_name,
                "exchanges": {rabbitmq_exchange_name: {"type": "direct"}},
            }
        },
    }


def test_rabbitmq_username_server(
    rabbitmq: Generator[RabbitMQ, None, None],
    rabbitmq_virtual_host_name: str,
) -> None:
    assert (
        "username"
        not in rabbitmq.config["virtual_hosts"][rabbitmq_virtual_host_name]
    )

    assert rabbitmq.username == rabbitmq.config["server"]["username"]


def test_rabbitmq_password_server(
    rabbitmq: Generator[RabbitMQ, None, None],
    rabbitmq_virtual_host_name: str,
) -> None:
    assert (
        "password"
        not in rabbitmq.config["virtual_hosts"][rabbitmq_virtual_host_name]
    )

    assert rabbitmq.password == rabbitmq.config["server"]["password"]


def test_rabbitmq_username_virtual_host_precedence(
    mocker: MockerFixture,
    rabbitmq: Generator[RabbitMQ, None, None],
    rabbitmq_virtual_host_name: str,
) -> None:
    mocker.patch.dict(
        rabbitmq.config["virtual_hosts"][rabbitmq_virtual_host_name],
        {"username": "username_takes_precedence"},
    )

    assert rabbitmq.username == "username_takes_precedence"


def test_rabbitmq_password_virtual_host_precedence(
    mocker: MockerFixture,
    rabbitmq: Generator[RabbitMQ, None, None],
    rabbitmq_virtual_host_name: str,
) -> None:
    mocker.patch.dict(
        rabbitmq.config["virtual_hosts"][rabbitmq_virtual_host_name],
        {"password": "password_takes_precedence"},
    )

    assert rabbitmq.password == "password_takes_precedence"


def test_rabbitmq_ssl_options_without_ssl(
    rabbitmq: Generator[RabbitMQ, None, None]
) -> None:
    assert rabbitmq.ssl_options is None


def test_rabbitmq_ssl_options_with_ssl(
    mocker: MockerFixture,
    rabbitmq_host: str,
    rabbitmq: Generator[RabbitMQ, None, None],
) -> None:
    mocker.patch.dict(rabbitmq.config["server"], {"ssl": True})

    assert isinstance(rabbitmq.ssl_options, pika.SSLOptions)
    assert rabbitmq.ssl_options.server_hostname == rabbitmq_host


def test_rabbitmq_connection(
    rabbitmq: Generator[RabbitMQ, None, None]
) -> None:
    assert isinstance(rabbitmq.connection, pika.BlockingConnection)
    assert rabbitmq.connection.is_open


def test_rabbitmq_exchanges(
    rabbitmq: Generator[RabbitMQ, None, None],
    rabbitmq_exchange_name: str,
) -> None:
    assert rabbitmq.exchanges == {rabbitmq_exchange_name: {"type": "direct"}}


def test_rabbitmq_channel(rabbitmq: Generator[RabbitMQ, None, None]) -> None:
    assert isinstance(
        rabbitmq.channel, pika.adapters.blocking_connection.BlockingChannel
    )
    assert rabbitmq.channel.connection == rabbitmq.connection


# def test_rabbitmq_qos(channels:dict,rabbitmq: Generator[RabbitMQ, None, None]) -> None:
#     print(channels)
#     raise Exception


def test_rabbitmq_queue_declare(
    queues: dict,
    rabbitmq_virtual_host_name: str,
    rabbitmq_queue_name: str,
) -> None:
    """Test RabbitMQ declared queue."""
    assert any(
        queue["vhost"] == rabbitmq_virtual_host_name
        and queue["name"] == rabbitmq_queue_name
        and queue["durable"]
        for queue in queues
    )


def test_rabbitmq_exchange_declare(
    exchanges: dict,
    rabbitmq_virtual_host_name: str,
    rabbitmq_exchange_name: str,
) -> None:
    """Test RabbitMQ declared exchange."""
    assert any(
        exchange["vhost"] == rabbitmq_virtual_host_name
        and exchange["name"] == rabbitmq_exchange_name
        and exchange["type"] == "direct"
        for exchange in exchanges
    )


def test_rabbitmq_binding(
    bindings: dict,
    rabbitmq_virtual_host_name: str,
    rabbitmq_exchange_name: str,
    rabbitmq_queue_name: str,
) -> None:
    """Test RabbitMQ bound exchange to queue."""
    assert any(
        binding["vhost"] == rabbitmq_virtual_host_name
        and binding["source"] == rabbitmq_exchange_name
        and binding["destination"] == rabbitmq_queue_name
        and binding["destination_type"] == "queue"
        for binding in bindings
    )
