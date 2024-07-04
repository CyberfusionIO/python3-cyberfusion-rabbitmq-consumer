"""Mock classes for use by tests.

This allows users of these classes to test without repeating stub classes for
mocking for each package.
"""

from typing import Any, Optional

import yaml


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

    def __init__(
        self, *, virtual_host_name: str, config_file_path: Optional[str]
    ) -> None:
        """Set attributes."""
        self.virtual_host_name = virtual_host_name

        if config_file_path:
            self.config = yaml.load(
                open(config_file_path, "r").read(), Loader=yaml.SafeLoader
            )
        else:
            self.config = None

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
