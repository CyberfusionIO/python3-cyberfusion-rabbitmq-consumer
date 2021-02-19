"""Program to interact with RabbitMQ."""

import os
import ssl
from typing import Optional

import pika
import yaml


class RabbitMQ:
    """Class to interact with RabbitMQ."""

    TYPE_EXCHANGE = "direct"

    def __init__(self, virtual_host: str):
        """Set attributes and call functions."""
        self.virtual_host = virtual_host

        self.set_config()
        self.set_ssl_options()
        self.set_connection()
        self.set_channel()
        self.declare_queue()
        self.declare_exchanges()

    def set_config(self) -> None:
        """Set config from YAML file."""
        path = os.path.join(
            os.path.sep, *["etc", "cyberfusion", "rabbitmq.yml"]
        )

        with open(path, "rb") as fh:
            self.config = yaml.load(fh.read(), Loader=yaml.SafeLoader)

    def set_ssl_options(self) -> None:
        """Set SSL options."""
        self.ssl_options: Optional[pika.SSLOptions] = None

        if self.config["server"]["ssl"]:
            self.ssl_options = pika.SSLOptions(
                ssl.create_default_context(), self.config["server"]["host"]
            )

    def set_connection(self) -> None:
        """Set RabbitMQ connection."""
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.config["server"]["host"],
                port=self.config["server"]["port"],
                virtual_host=self.virtual_host,
                credentials=pika.credentials.PlainCredentials(
                    self.config["server"]["username"],
                    self.config["server"]["password"],
                ),
            )
        )

    def set_channel(self) -> None:
        """Set RabbitMQ channel."""
        self.channel = self.connection.channel()

    def declare_queue(self) -> None:
        """Declare volatile (exclusive) RabbitMQ queue."""
        self.queue_name = self.channel.queue_declare(
            queue="", exclusive=True
        ).method.queue

    def declare_exchanges(self) -> None:
        """Declare RabbitMQ exchanges and bind to queue."""
        for virtual_host in self.config["virtual_hosts"]:
            for exchange, values in virtual_host["exchanges"]:
                # Declare exchange

                self.channel.exchange_declare(
                    exchange=exchange, exchange_type=self.TYPE_EXCHANGE
                )

                # Bind to queue for each routing key

                for routing_key in values["routing_keys"]:
                    self.channel.queue_bind(
                        exchange=exchange,
                        queue=self.queue_name,
                        routing_key=routing_key,
                    )
