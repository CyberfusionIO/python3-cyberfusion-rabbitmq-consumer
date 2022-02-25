from cyberfusion.RabbitMQConsumer.RabbitMQ import get_config_file_path


def test_config_file_path() -> None:
    """Test config file path."""
    assert get_config_file_path() == "/etc/cyberfusion/rabbitmq.yml"
