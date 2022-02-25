import pytest

from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ


@pytest.fixture
def rabbitmq() -> RabbitMQ:
    return RabbitMQ(virtual_host_name="test")
