import functools

import pika
from pytest_mock import MockerFixture  # type: ignore[attr-defined]

from cyberfusion.RabbitMQConsumer.tests import (
    Channel,
    Lock,
    Method,
    Properties,
    RabbitMQ,
)
from cyberfusion.RabbitMQConsumer.utilities import (
    _prefix_message,
    finish_handle,
    prepare_handle,
)


def test_prefix_message_with_prefix() -> None:
    assert _prefix_message("prefix", "suffix") == "[prefix] suffix"


def test_prefix_message_without_prefix() -> None:
    assert _prefix_message(None, "suffix") == "suffix"


def test_prepare_handle(
    mocker: MockerFixture, rabbitmq_exchange_name: str
) -> None:
    # Create test objects

    lock = Lock()

    # Set spies

    spy_acquire = mocker.spy(Lock, "acquire")

    # Call function

    prepare_handle(lock=lock, exchange_name=rabbitmq_exchange_name)

    # Test acquire was called

    spy_acquire.assert_called_once_with(mocker.ANY)


def test_finish_handle(
    mocker: MockerFixture, rabbitmq_exchange_name: str
) -> None:
    # Create test objects

    rabbitmq = RabbitMQ()
    channel = Channel()
    properties = Properties()
    lock = Lock()
    method = Method(exchange_name=rabbitmq_exchange_name)

    # Set spies

    spy_release = mocker.spy(Lock, "release")
    spy_add_callback_threadsafe = mocker.spy(
        rabbitmq.connection, "add_callback_threadsafe"
    )

    # Call function

    finish_handle(
        rabbitmq=rabbitmq,
        channel=channel,
        method=method,
        properties=properties,
        lock=lock,
        body={"a": "b"},
        exchange_name=rabbitmq_exchange_name,
    )

    # Test lock release was called

    spy_release.assert_called_once_with(mocker.ANY)

    # Test callback calls

    spy_add_callback_threadsafe.call_args_list[0] == functools.partial(
        channel.basic_publish,
        exchange=rabbitmq_exchange_name,
        routing_key=properties.reply_to,
        properties=pika.BasicProperties(
            correlation_id=properties.correlation_id,
            content_type="application/json",
        ),
        body='{"a": "b"}',
    )

    spy_add_callback_threadsafe.call_args_list[1] == mocker.call(
        functools.partial(channel.basic_ack, delivery_tag="fake")
    )

    spy_add_callback_threadsafe.call_count == 2
