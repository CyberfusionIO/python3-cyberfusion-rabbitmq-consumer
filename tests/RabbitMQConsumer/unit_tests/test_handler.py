import functools
import logging
from typing import Generator

import pika
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockerFixture  # type: ignore[attr-defined]

from cyberfusion.RabbitMQConsumer.contracts import (
    RPCRequestBase,
    RPCResponseBase,
    RPCResponseData,
)
from cyberfusion.RabbitMQConsumer.handler import Handler
from cyberfusion.RabbitMQConsumer.tests import (
    Channel,
    Lock,
    Method,
    Properties,
    RabbitMQ,
)

logger = logging.getLogger(__name__)


class TestHandleModuleSuccess:
    class Handler:
        def __call__(
            request: RPCRequestBase,
        ) -> RPCResponseBase:
            return RPCResponseBase(
                success=True, message="Did it!", data=RPCResponseData()
            )


class TestHandleModuleException:
    class Handler:
        def __call__(
            request: RPCRequestBase,
        ) -> dict:
            raise Exception


def test_handler_calls(
    mocker: MockerFixture,
    rabbitmq_exchange_name: str,
    rabbitmq_virtual_host_name: str,
    rabbitmq_consumer_config_file_path: Generator[str, None, None],
) -> None:
    rabbitmq = RabbitMQ(
        virtual_host_name=rabbitmq_virtual_host_name,
        config_file_path=rabbitmq_consumer_config_file_path,
    )
    channel = Channel()
    properties = Properties()
    lock = Lock()
    method = Method(exchange_name=rabbitmq_exchange_name)

    spy_acquire = mocker.spy(Lock, "acquire")
    spy_release = mocker.spy(Lock, "release")
    spy_add_callback_threadsafe = mocker.spy(
        rabbitmq.connection, "add_callback_threadsafe"
    )

    Handler(
        module=TestHandleModuleSuccess,
        rabbitmq=rabbitmq,
        channel=channel,
        method=method,
        properties=properties,
        lock=lock,
        request=RPCRequestBase(),
    )()

    spy_acquire.assert_called_once_with(mocker.ANY)
    spy_release.assert_called_once_with(mocker.ANY)
    spy_add_callback_threadsafe.call_args_list[0] == functools.partial(
        channel.basic_publish,
        exchange=rabbitmq_exchange_name,
        routing_key=properties.reply_to,
        properties=pika.BasicProperties(
            correlation_id=properties.correlation_id,
            content_type="application/json",
        ),
        body='{"success": True, "message": "Did it!", "data": {}}',
    )
    spy_add_callback_threadsafe.call_args_list[1] == mocker.call(
        functools.partial(channel.basic_ack, delivery_tag="fake")
    )
    spy_add_callback_threadsafe.call_count == 2


def test_handler_uncaught_exception(
    mocker: MockerFixture,
    caplog: LogCaptureFixture,
    rabbitmq_exchange_name: str,
    rabbitmq_virtual_host_name: str,
    rabbitmq_consumer_config_file_path: Generator[str, None, None],
) -> None:
    rabbitmq = RabbitMQ(
        virtual_host_name=rabbitmq_virtual_host_name,
        config_file_path=rabbitmq_consumer_config_file_path,
    )
    channel = Channel()
    properties = Properties()
    lock = Lock()
    method = Method(exchange_name=rabbitmq_exchange_name)

    with caplog.at_level(logging.ERROR):
        Handler(
            module=TestHandleModuleException,
            rabbitmq=rabbitmq,
            channel=channel,
            method=method,
            properties=properties,
            lock=lock,
            request=RPCRequestBase(),
        )()

    assert "Unhandled exception occurred" in caplog.text
