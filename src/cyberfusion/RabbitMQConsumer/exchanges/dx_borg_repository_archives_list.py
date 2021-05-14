"""Methods for exchange."""

import json

import pika

from cyberfusion.BorgSupport.repositories import Repository
from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ


def handle(
    rabbitmq: RabbitMQ,
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
    json_body: dict,
) -> None:
    """Handle message."""  # noqa: D202

    # Set variables

    passphrase = json_body["passphrase"]
    path = json_body["path"]
    identity_file_path = json_body["identity_file_path"]
    uid = json_body["unix_id"]
    gid = json_body["unix_id"]

    # Get object

    repository = Repository(path, passphrase, uid, gid, identity_file_path)

    # Get archives

    print(f"Getting archives for Borg repository with path '{path}'")

    try:
        archives = repository.list()

        print(
            f"Success getting archives for Borg repository with path '{path}'"
        )
    except Exception as e:
        # If action fails, don't crash entire program

        print(
            f"Error getting archives for Borg repository with path '{path}': {e}"  # noqa: E501
        )

    # Publish message

    channel.basic_publish(
        exchange=method.exchange,
        routing_key=properties.reply_to,
        properties=pika.BasicProperties(
            correlation_id=properties.correlation_id,
        ),
        body=json.dumps(archives),
    )
