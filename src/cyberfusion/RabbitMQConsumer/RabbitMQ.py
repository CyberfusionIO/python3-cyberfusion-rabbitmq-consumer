"""Program to interact with RabbitMQ."""

import os
import ssl
from typing import Optional

import pika
import yaml


class RabbitMQ:
    """Class to interact with RabbitMQ."""

    def __init__(self, virtual_host_name: str):
        """Set attributes and call functions."""
        self.virtual_host_name = virtual_host_name

        self.set_config()
        self.set_ssl_options()
        self.set_connection()
        self.set_channel()
        self.declare_queue()
        self.declare_exchanges()
        self.bind_queue()

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
                virtual_host=self.virtual_host_name,
                credentials=pika.credentials.PlainCredentials(
                    self.config["server"]["username"],
                    self.config["server"]["password"],
                ),
                ssl_options=self.ssl_options,
            )
        )

    def set_channel(self) -> None:
        """Set RabbitMQ channel."""
        self.channel = self.connection.channel()

    def declare_queue(self) -> None:
        """Declare RabbitMQ queue."""
        self.channel.queue_declare(
            queue=self.config["virtual_hosts"][self.virtual_host_name][
                "queue"
            ],
            durable=True,
        )

    def declare_exchanges(self) -> None:
        """Declare RabbitMQ exchanges."""
        for exchange_name, exchange_values in self.config["virtual_hosts"][
            self.virtual_host_name
        ]["exchanges"].items():
            self.channel.exchange_declare(
                exchange=exchange_name, exchange_type=exchange_values["type"]
            )

    def bind_queue(self) -> None:
        """Bind to RabbitMQ queue at each exchange."""
        for exchange_name, _exchange_values in self.config["virtual_hosts"][
            self.virtual_host_name
        ]["exchanges"].items():
            queue = self.config["virtual_hosts"][self.virtual_host_name][
                "queue"
            ]

            print(f"Binding: exchange '{exchange_name}', queue '{queue}'")

            self.channel.queue_bind(exchange=exchange_name, queue=queue)
