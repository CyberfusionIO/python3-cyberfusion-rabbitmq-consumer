"""Config."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

import yaml
from cached_property import cached_property

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


class Config:
    """Base config."""

    def __init__(self, path: str) -> None:
        """Path to config file."""
        self.path = path

    @cached_property  # type: ignore[misc]
    def _contents(self) -> dict:
        """Set config from YAML file."""
        with open(self.path, "rb") as fh:
            return yaml.load(fh.read(), Loader=yaml.SafeLoader)

    @property
    def server(self) -> Server:
        """Get server config."""
        return Server(**self._contents["server"])

    @property
    def virtual_hosts(self) -> List[VirtualHost]:
        """Get virtual host configs."""
        virtual_hosts = []

        for virtual_host_name, virtual_host_properties in self._contents[
            "virtual_hosts"
        ].items():
            exchanges = []

            for exchange_name, exchange_properties in virtual_host_properties[
                "exchanges"
            ].items():
                exchanges.append(
                    Exchange(
                        name=exchange_name, type=exchange_properties["type"]
                    )
                )

            virtual_hosts.append(
                VirtualHost(
                    name=virtual_host_name,
                    queue=virtual_host_properties["queue"],
                    fernet_key=virtual_host_properties["fernet_key"],
                    exchanges=exchanges,
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
