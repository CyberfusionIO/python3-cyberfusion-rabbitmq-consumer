"""Config."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

import yaml
from functools import cached_property

from cyberfusion.RabbitMQConsumer.exceptions import VirtualHostNotExistsError


class ExchangeType(str, Enum):
    """Exchange types."""

    DIRECT = "direct"


@dataclass
class Server:
    """Server."""

    host: str
    password: str
    port: int
    ssl: bool
    username: str


@dataclass
class LogServer:
    """Log server."""

    base_url: str
    api_token: str


@dataclass
class Exchange:
    """Exchange."""

    name: str
    type: ExchangeType


@dataclass
class VirtualHost:
    """Virtual host."""

    name: str
    exchanges: List[Exchange]
    queue: str
    fernet_key: Optional[str] = None
    max_simultaneous_requests: int = 5


class Config:
    """Base config."""

    KEY_NAME = "name"
    KEY_QUEUE = "queue"
    KEY_FERNET_KEY = "fernet_key"
    KEY_EXCHANGES = "exchanges"
    KEY_MAX_SIMULTANEOUS_REQUESTS = "max_simultaneous_requests"

    def __init__(self, path: str) -> None:
        """Path to config file."""
        self.path = path

    @cached_property
    def _contents(self) -> dict:
        """Set config from YAML file."""
        with open(self.path, "rb") as fh:
            return yaml.load(fh.read(), Loader=yaml.SafeLoader)

    @property
    def server(self) -> Server:
        """Get server config."""
        return Server(**self._contents["server"])

    @property
    def mock(self) -> bool:
        return self._contents.get("mock", False)

    @property
    def log_server(self) -> Optional[LogServer]:
        """Get log server config."""
        if "log_server" not in self._contents:
            return None

        return LogServer(**self._contents["log_server"])

    @property
    def virtual_hosts(self) -> List[VirtualHost]:
        """Get virtual host configs."""
        virtual_hosts = []

        for virtual_host_name, virtual_host_properties in self._contents[
            "virtual_hosts"
        ].items():
            # Get exchanges

            exchanges = []

            for exchange_name, exchange_properties in virtual_host_properties[
                "exchanges"
            ].items():
                exchanges.append(
                    Exchange(name=exchange_name, type=exchange_properties["type"])
                )

            # Get arguments

            arguments = {
                self.KEY_NAME: virtual_host_name,
                self.KEY_QUEUE: virtual_host_properties[self.KEY_QUEUE],
                self.KEY_FERNET_KEY: virtual_host_properties[self.KEY_FERNET_KEY],
                self.KEY_EXCHANGES: exchanges,
            }

            if self.KEY_MAX_SIMULTANEOUS_REQUESTS in virtual_host_properties:
                arguments[self.KEY_MAX_SIMULTANEOUS_REQUESTS] = virtual_host_properties[
                    self.KEY_MAX_SIMULTANEOUS_REQUESTS
                ]

            # Add virtual host

            virtual_hosts.append(
                VirtualHost(
                    **arguments,
                )
            )

        return virtual_hosts

    def get_virtual_host(self, name: str) -> VirtualHost:
        """Get virtual host config by name."""
        for virtual_host in self.virtual_hosts:
            if virtual_host.name != name:
                continue

            return virtual_host

        raise VirtualHostNotExistsError

    def get_all_exchanges(self) -> List[Exchange]:
        """Get exchanges for all virtual hosts."""
        exchanges = []

        for virtual_host in self.virtual_hosts:
            exchanges.extend(virtual_host.exchanges)

        return exchanges
