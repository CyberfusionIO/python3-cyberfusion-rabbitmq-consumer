"""Program to interact with RabbitMQ."""

import logging
import os
import ssl
from typing import Dict, List, Optional, Union

import pika
import yaml

logger = logging.getLogger(__name__)

NAME_ENVIRONMENT_VARIABLE_CONFIG_FILE_PATH = (
    "RABBITMQ_CONSUMER_CONFIG_FILE_PATH"
)

# Keep in sync with Cluster API

FERNET_TOKEN_KEYS = [
    "secret_values",
    "passphrase",
    "password",
    "admin_password",
    "database_user_password",
]

# Every message is handled in its own thread, so this is the max amount of threads

HANDLE_SIMULTANEOUS_MAX = 5


def get_config_file_path() -> str:
    """Get config file path."""
    return os.environ[NAME_ENVIRONMENT_VARIABLE_CONFIG_FILE_PATH]


class RabbitMQ:
    """Class to interact with RabbitMQ."""

    def __init__(self, virtual_host_name: str):
        """Set attributes and call functions."""
        self.virtual_host_name = virtual_host_name

        self.set_config()
        self.set_connection()
        self.set_channel()
        self.declare_queue()
        self.declare_exchanges()
        self.bind_queue()
        self.set_basic_qos()

    def set_config(self) -> None:
        """Set config from YAML file."""
        with open(get_config_file_path(), "rb") as fh:
            self.config = yaml.load(fh.read(), Loader=yaml.SafeLoader)

    @property
    def ssl_options(self) -> Optional[pika.SSLOptions]:
        """Set SSL options."""
        if not self.config["server"]["ssl"]:
            return None

        return pika.SSLOptions(
            ssl.create_default_context(), self.config["server"]["host"]
        )

    @property
    def username(self) -> None:
        """Set username."""
        if "username" in self.config["virtual_hosts"][self.virtual_host_name]:
            return self.config["virtual_hosts"][self.virtual_host_name][
                "username"
            ]

        return self.config["server"]["username"]

    @property
    def password(self) -> None:
        """Set password."""
        if "password" in self.config["virtual_hosts"][self.virtual_host_name]:
            return self.config["virtual_hosts"][self.virtual_host_name][
                "password"
            ]

        return self.config["server"]["password"]

    @property
    def fernet_key(self) -> Optional[str]:
        """Set Fernet key."""
        if (
            "fernet_key"
            in self.config["virtual_hosts"][self.virtual_host_name]
        ):
            return self.config["virtual_hosts"][self.virtual_host_name][
                "fernet_key"
            ]

        return None

    def set_connection(self) -> None:
        """Set RabbitMQ connection."""
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.config["server"]["host"],
                port=self.config["server"]["port"],
                virtual_host=self.virtual_host_name,
                credentials=pika.credentials.PlainCredentials(
                    self.username, self.password
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

    @property
    def exchanges(self) -> Dict[str, Dict[str, Union[str, List[str]]]]:
        """Get exchanges from config."""
        return self.config["virtual_hosts"][self.virtual_host_name][
            "exchanges"
        ]

    def declare_exchanges(self) -> None:
        """Declare RabbitMQ exchanges."""
        for exchange_name, exchange_values in self.exchanges.items():
            self.channel.exchange_declare(
                exchange=exchange_name, exchange_type=exchange_values["type"]
            )

    def bind_queue(self) -> None:
        """Bind to RabbitMQ queue at each exchange."""
        for exchange_name, _exchange_values in self.exchanges.items():
            queue = self.config["virtual_hosts"][self.virtual_host_name][
                "queue"
            ]

            logger.info(
                f"Binding: exchange '{exchange_name}', queue '{queue}', virtual host '{self.virtual_host_name}'"
            )

            self.channel.queue_bind(exchange=exchange_name, queue=queue)

    def set_basic_qos(self) -> None:
        """Set basic QoS for channel."""
        self.channel.basic_qos(prefetch_count=HANDLE_SIMULTANEOUS_MAX)
