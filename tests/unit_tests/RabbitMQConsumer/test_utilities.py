from cyberfusion.RabbitMQConsumer.utilities import _prefix_message


def test_prefix_message_with_prefix() -> None:
    assert _prefix_message("prefix", "suffix") == "[prefix] suffix"


def test_prefix_message_without_prefix() -> None:
    assert _prefix_message(None, "suffix") == "suffix"
