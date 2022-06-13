"""Mock classes for use by tests.

This allows users of these classes to test without repeating stub classes for
mocking for each package.
"""

from typing import Any


class Connection:
    """Fake implementation of pika.BlockingConnection."""

    def __init__(self) -> None:
        """Do nothing."""
        pass

    def add_callback_threadsafe(self, *args: Any, **kwargs: Any) -> None:
        """Do nothing."""
        pass


class RabbitMQ:
    """Fake implementation of RabbitMQ.RabbitMQ."""

    def __init__(self) -> None:
        """Set attributes."""
        self.connection = Connection()


class Channel:
    """Fake implementation of pika.adapters.blocking_connection.BlockingChannel."""

    def __init__(self) -> None:
        """Do nothing."""
        pass

    def basic_publish(self) -> None:
        """Do nothing."""
        pass

    def basic_ack(self) -> None:
        """Do nothing."""
        pass


class Method:
    """Fake implementation of pika.spec.Basic.Deliver."""

    def __init__(self, *, exchange_name: str) -> None:
        """Set attributes."""
        self.exchange = exchange_name
        self.delivery_tag = "fake"


class Properties:
    """Fake implementation of pika.spec.BasicProperties."""

    reply_to = "fake"
    correlation_id = "fake"


class Lock:
    """Fake implementation of threading.Lock."""

    def __init__(self) -> None:
        """Do nothing."""
        pass

    def acquire(self) -> None:
        """Do nothing."""
        pass

    def release(self) -> None:
        """Do nothing."""
        pass


def get_handle_parameters(exchange_name: str, *, json_body: dict) -> dict:
    """Get parameters for testing handle() method of exchange module."""
    return {
        "rabbitmq": RabbitMQ(),
        "channel": Channel(),
        "method": Method(exchange_name=exchange_name),
        "properties": Properties(),
        "lock": Lock(),
        "json_body": json_body,
    }
