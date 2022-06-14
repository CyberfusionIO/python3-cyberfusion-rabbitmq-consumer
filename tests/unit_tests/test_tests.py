from cyberfusion.RabbitMQConsumer.tests import (
    Channel,
    Connection,
    Lock,
    Method,
    Properties,
    RabbitMQ,
    get_handle_parameters,
)


def test_rabbitmq_test_class(
    rabbitmq_virtual_host_name: str, rabbitmq_consumer_config_file_path: str
):
    rabbitmq = RabbitMQ(
        virtual_host_name=rabbitmq_virtual_host_name,
        config_file_path=rabbitmq_consumer_config_file_path,
    )

    assert rabbitmq.virtual_host_name == rabbitmq_virtual_host_name
    assert isinstance(rabbitmq.config, dict)
    assert isinstance(rabbitmq.connection, Connection)


def test_connection_test_class():
    connection = Connection()

    assert isinstance(connection, Connection)

    connection.add_callback_threadsafe()


def test_lock_test_class():
    lock = Lock()

    assert isinstance(lock, Lock)

    lock.acquire()
    lock.release()


def test_channel_test_class():
    channel = Channel()

    assert isinstance(channel, Channel)

    channel.basic_publish()
    channel.basic_ack()


def test_method_test_class(rabbitmq_exchange_name: str):
    method = Method(exchange_name=rabbitmq_exchange_name)

    assert isinstance(method, Method)
    assert method.exchange == rabbitmq_exchange_name
    assert method.delivery_tag == "fake"


def test_properties_test_class(rabbitmq_exchange_name: str):
    properties = Properties()

    assert isinstance(properties, Properties)
    assert properties.reply_to == "fake"
    assert properties.correlation_id == "fake"


def test_get_handle_parameters(
    rabbitmq_exchange_name: str,
    rabbitmq_virtual_host_name: str,
    rabbitmq_consumer_config_file_path: str,
):
    rabbitmq = RabbitMQ(
        virtual_host_name=rabbitmq_virtual_host_name,
        config_file_path=rabbitmq_consumer_config_file_path,
    )

    handle_parameters = get_handle_parameters(
        exchange_name=rabbitmq_exchange_name,
        rabbitmq=rabbitmq,
        json_body={"a": "b"},
    )

    assert handle_parameters["exchange_name"] == rabbitmq_exchange_name
    assert handle_parameters["virtual_host_name"] == rabbitmq_virtual_host_name
    assert isinstance(handle_parameters["rabbitmq_config"], dict)
    assert handle_parameters["json_body"] == {"a": "b"}
