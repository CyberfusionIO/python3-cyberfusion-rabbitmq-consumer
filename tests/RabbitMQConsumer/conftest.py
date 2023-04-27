import os
from typing import Generator

import pytest
import requests
import yaml
from pytest_mock import MockerFixture  # type: ignore[attr-defined]

from cyberfusion.Common import get_tmp_file
from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ


@pytest.fixture(scope="session")
def rabbitmq_virtual_host_name() -> str:
    return os.environ["RABBITMQ_VIRTUAL_HOST_NAME"]


@pytest.fixture(scope="session")
def rabbitmq_username() -> str:
    return os.environ["RABBITMQ_USERNAME"]


@pytest.fixture(scope="session")
def rabbitmq_password() -> str:
    return os.environ["RABBITMQ_PASSWORD"]


@pytest.fixture(scope="session")
def rabbitmq_host() -> str:
    return os.environ["RABBITMQ_HOST"]


@pytest.fixture(scope="session")
def rabbitmq_fernet_key() -> str:
    return os.environ.get(
        "RABBITMQ_FERNET_KEY", "ZEp4ttRkU-IvB6n0yfjW2_uvL4jhgt837o4h-b_HELI="
    )


@pytest.fixture(scope="session")
def rabbitmq_amqp_port() -> int:
    return int(os.environ["RABBITMQ_AMQP_PORT"])


@pytest.fixture(scope="session")
def rabbitmq_management_port() -> int:
    return int(os.environ["RABBITMQ_MANAGEMENT_PORT"])


@pytest.fixture(scope="session")
def rabbitmq_ssl() -> bool:
    return os.environ["RABBITMQ_SSL"] == "true"


@pytest.fixture(scope="session")
def rabbitmq_exchange_name() -> str:
    return "dx_test"


@pytest.fixture(scope="session")
def rabbitmq_queue_name(rabbitmq_virtual_host_name: str) -> str:
    return rabbitmq_virtual_host_name


@pytest.fixture(scope="session")
def rabbitmq_protocol(rabbitmq_ssl: bool) -> str:
    if rabbitmq_ssl:
        return "https"

    return "http"


@pytest.fixture(scope="session")
def rabbitmq_management_url(
    rabbitmq_protocol: str, rabbitmq_host: str, rabbitmq_management_port: int
) -> str:
    return (
        f"{rabbitmq_protocol}://{rabbitmq_host}:{rabbitmq_management_port}/api"
    )


@pytest.fixture(autouse=True)
def rabbitmq_consumer_config_file_path(
    mocker: MockerFixture,
    rabbitmq_host: str,
    rabbitmq_username: str,
    rabbitmq_password: str,
    rabbitmq_amqp_port: int,
    rabbitmq_ssl: bool,
    rabbitmq_virtual_host_name: str,
    rabbitmq_exchange_name: str,
    rabbitmq_queue_name: str,
    rabbitmq_fernet_key: str,
) -> Generator[str, None, None]:
    path = get_tmp_file()
    config = {
        "server": {
            "host": rabbitmq_host,
            "username": rabbitmq_username,
            "password": rabbitmq_password,
            "port": rabbitmq_amqp_port,
            "ssl": rabbitmq_ssl,
        },
        "virtual_hosts": {
            rabbitmq_virtual_host_name: {
                "fernet_key": rabbitmq_fernet_key,
                "queue": rabbitmq_queue_name,
                "exchanges": {rabbitmq_exchange_name: {"type": "direct"}},
            }
        },
    }

    with open(path, "w") as f:
        f.write(
            yaml.dump(
                config,
                explicit_start=True,
                default_flow_style=False,
            )
        )

    mocker.patch(
        "cyberfusion.RabbitMQConsumer.RabbitMQ.get_config_file_path",
        return_value=path,
    )

    yield path

    os.unlink(path)


@pytest.fixture
def queues(
    rabbitmq: Generator[RabbitMQ, None, None],
    rabbitmq_management_url: str,
    rabbitmq_queue_name: str,
    rabbitmq_username: str,
    rabbitmq_password: str,
) -> dict:
    r = requests.get(
        f"{rabbitmq_management_url}/queues/{rabbitmq_queue_name}",
        auth=(rabbitmq_username, rabbitmq_password),
    )

    return r.json()


@pytest.fixture
def exchanges(
    rabbitmq: Generator[RabbitMQ, None, None],
    rabbitmq_management_url: str,
    rabbitmq_queue_name: str,
    rabbitmq_username: str,
    rabbitmq_password: str,
) -> dict:
    r = requests.get(
        f"{rabbitmq_management_url}/exchanges/{rabbitmq_queue_name}",
        auth=(rabbitmq_username, rabbitmq_password),
    )

    r.raise_for_status()

    return r.json()


@pytest.fixture
def bindings(
    rabbitmq: Generator[RabbitMQ, None, None],
    rabbitmq_management_url: str,
    rabbitmq_queue_name: str,
    rabbitmq_exchange_name: str,
    rabbitmq_username: str,
    rabbitmq_password: str,
) -> dict:
    r = requests.get(
        f"{rabbitmq_management_url}/exchanges/{rabbitmq_queue_name}/{rabbitmq_exchange_name}/bindings/source",
        auth=(rabbitmq_username, rabbitmq_password),
    )

    r.raise_for_status()

    return r.json()


@pytest.fixture
def virtual_hosts(
    rabbitmq: Generator[RabbitMQ, None, None],
    rabbitmq_management_url: str,
    rabbitmq_username: str,
    rabbitmq_password: str,
) -> dict:
    r = requests.get(
        f"{rabbitmq_management_url}/vhosts",
        auth=(rabbitmq_username, rabbitmq_password),
    )

    r.raise_for_status()

    return r.json()


# @pytest.fixture
# def channels(
#     rabbitmq: Generator[RabbitMQ, None, None],
#     rabbitmq_management_url: str,
#     rabbitmq_username: str,
#     rabbitmq_password: str,rabbitmq_virtual_host_name:str
# ) -> dict:
#     r= requests.get(
#         # f"{rabbitmq_management_url}/vhosts/{rabbitmq_virtual_host_name}/channels",
#         f"{rabbitmq_management_url}/connections",
#         auth=(rabbitmq_username, rabbitmq_password),
#     )

#     r.raise_for_status()

#     return r.json()


@pytest.fixture
def rabbitmq(
    rabbitmq_username: str,
    rabbitmq_password: str,
    rabbitmq_management_url: str,
    rabbitmq_virtual_host_name: str,
) -> Generator[RabbitMQ, None, None]:
    # Create virtual host if it doesn't exist yet. When running in CI, the virtual
    # host should already exist, and the user has no permissions to create it,
    # so we don't want to create it then. When running locally, the virtual host
    # may or may not exist, and the user should have permissions to create it.

    _virtual_hosts = requests.get(
        f"{rabbitmq_management_url}/vhosts",
        auth=(rabbitmq_username, rabbitmq_password),
    )

    _virtual_hosts.raise_for_status()

    virtual_hosts = _virtual_hosts.json()

    if not any(
        virtual_host["name"] == rabbitmq_virtual_host_name
        for virtual_host in virtual_hosts
    ):
        requests.put(
            f"{rabbitmq_management_url}/vhosts/{rabbitmq_virtual_host_name}",
            auth=(rabbitmq_username, rabbitmq_password),
        ).raise_for_status()
    # requests.put(  # Do not need to set permissions, as user should already have administrator tag (local) or permissions (CI)
    #         f"{rabbitmq_management_url}/permissions/{rabbitmq_virtual_host_name}/{rabbitmq_username}",data={"configure":".*","write":".*","read":".*"},
    #         auth=(rabbitmq_username, rabbitmq_password),
    #     ).raise_for_status()

    try:
        yield RabbitMQ(virtual_host_name=rabbitmq_virtual_host_name)
    finally:
        # Initialising the RabbitMQ object creates many objects within the given
        # virtual host. By deleting the virtual host, all associated objects
        # should be deleted as well, leaving us with the state of the RabbitMQ
        # instance before running tests.

        requests.delete(
            f"{rabbitmq_management_url}/vhosts/{rabbitmq_virtual_host_name}",
            auth=(rabbitmq_username, rabbitmq_password),
        ).raise_for_status()
