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
    """Handle message."""

    # Set variables

    remote_url = json_body["remote_url"]
    passphrase = json_body["passphrase"]
    identity_file_path = json_body["identity_file_path"]

    # Get object

    repository = Repository(
        remote_url,
        passphrase,
        identity_file_path,
    )

    # Get archives

    print(
        f"Getting archives for Borg repository with remote URL '{remote_url}'"
    )

    try:
        archives = repository.list()

        print(
            f"Success getting archives for Borg repository with remote URL '{remote_url}'"
        )
    except Exception as e:
        # If action fails, don't crash entire program

        print(
            f"Error getting archives for Borg repository with remote URL '{remote_url}': {e}"
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
