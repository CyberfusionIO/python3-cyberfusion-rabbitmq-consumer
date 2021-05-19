"""Methods for exchange."""

import json

import pika

from cyberfusion.BorgSupport.repositories import Repository
from cyberfusion.ClusterSupport import ClusterSupport
from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ


def handle(
    rabbitmq: RabbitMQ,
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
    json_body: dict,
) -> None:
    """Handle message."""  # noqa: D202

    # Get support object

    support = ClusterSupport()

    # Get API object

    obj = support.get_borg_repositories(id_=json_body["borg_repository_id"])[0]

    # Get object

    repository = Repository(
        obj.remote_url,
        obj.passphrase,
        obj.unix_user.unix_id,
        obj.unix_user.unix_id,
        obj.ssh_key.identity_file_path,
    )

    # Get archives

    print(
        f"Getting archives for Borg repository with remote URL '{obj.remote_url}'"  # noqa: E501
    )

    try:
        archives = repository.list()

        print(
            f"Success getting archives for Borg repository with remote URL '{obj.remote_url}'"  # noqa: E501
        )
    except Exception as e:
        # If action fails, don't crash entire program

        print(
            f"Error getting archives for Borg repository with remote URL '{obj.remote_url}': {e}"  # noqa: E501
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
