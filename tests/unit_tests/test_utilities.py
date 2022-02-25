from cyberfusion.RabbitMQConsumer.utilities import _prefix_message


def test_prefix_message() -> None:
    """Test prefix message."""
    assert _prefix_message("prefix", "suffix") == "[prefix] suffix"
