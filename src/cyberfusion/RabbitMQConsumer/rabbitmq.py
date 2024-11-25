"""Program to interact with RabbitMQ."""

import logging
from typing import Optional

import pika

from cyberfusion.RabbitMQConsumer.config import Config
from cyberfusion.RabbitMQConsumer.utilities import get_pika_ssl_options

logger = logging.getLogger(__name__)


class RabbitMQ:
    """Class to interact with RabbitMQ."""

    def __init__(self, virtual_host_name: str, config: Config) -> None:
        """Set attributes and call functions."""
        self.virtual_host_name = virtual_host_name
        self.config = config

        self.virtual_host_config = self.config.get_virtual_host(self.virtual_host_name)

        self.set_connection()
        self.set_channel()
        self.declare_queue()
        self.declare_exchanges()
        self.bind_queue()
        self.set_basic_qos()

    @property
    def fernet_key(self) -> Optional[str]:
        """Set Fernet key."""
        if not self.virtual_host_config.fernet_key:
            return None

        return self.virtual_host_config.fernet_key

    def set_connection(self) -> None:
        """Set RabbitMQ connection."""
        arguments = {
            "host": self.config.server.host,
            "port": self.config.server.port,
            "virtual_host": self.virtual_host_name,
            "credentials": pika.credentials.PlainCredentials(
                self.config.server.username, self.config.server.password
            ),
        }

        if self.config.server.ssl:
            arguments["ssl_options"] = get_pika_ssl_options(self.config.server.host)

        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                **arguments,
            )
        )

    def set_channel(self) -> None:
        """Set RabbitMQ channel."""
        self.channel = self.connection.channel()

    def declare_queue(self) -> None:
        """Declare RabbitMQ queue."""
        self.channel.queue_declare(
            queue=self.virtual_host_config.queue,
            durable=True,
        )

    def declare_exchanges(self) -> None:
        """Declare RabbitMQ exchanges."""
        for exchange in self.virtual_host_config.exchanges:
            self.channel.exchange_declare(
                exchange=exchange.name, exchange_type=exchange.type
            )

    def bind_queue(self) -> None:
        """Bind to RabbitMQ queue at each exchange."""
        for exchange in self.virtual_host_config.exchanges:
            queue = self.virtual_host_config.queue

            logger.info(
                "Binding: exchange '%s', queue '%s', virtual host '%s'",
                exchange.name,
                queue,
                self.virtual_host_name,
            )

            self.channel.queue_bind(exchange=exchange.name, queue=queue)

    def set_basic_qos(self) -> None:
        """Set basic QoS for channel."""
        self.channel.basic_qos(
            prefetch_count=self.virtual_host_config.max_simultaneous_requests
        )
