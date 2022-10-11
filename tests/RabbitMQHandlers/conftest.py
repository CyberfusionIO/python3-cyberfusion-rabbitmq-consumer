import pytest

from cyberfusion.RabbitMQConsumer.tests import get_handle_parameters


@pytest.fixture
def handle_parameters(request: tuple) -> dict:
    exchange_name, virtual_host_name, json_body = request.param

    return get_handle_parameters(
        exchange_name=exchange_name,
        virtual_host_name=virtual_host_name,
        config_file_path=None,
        json_body=json_body,
    )
