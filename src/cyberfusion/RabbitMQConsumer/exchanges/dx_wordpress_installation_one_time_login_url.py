"""Methods for exchange."""

import json

import pika

from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ
from cyberfusion.WordPressSupport import Installation
from cyberfusion.WordPressSupport.users import User, Users


def handle(
    rabbitmq: RabbitMQ,
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
    json_body: dict,
) -> None:
    """Handle message."""  # noqa: D202

    # Set variables

    path = json_body["path"]
    home = json_body["home"]
    uid = json_body["unix_id"]
    gid = json_body["unix_id"]

    # Get object

    installation = Installation(path, uid, gid, home)

    # Get administrator users

    users = Users(installation).get(role=User.NAME_ROLE_ADMINISTRATOR)

    # Pick first user

    user = users[0]

    # Get one time login URL

    print(
        f"Getting one time login URL for installation with path '{path}', user with ID '{user.id}'"  # noqa: E501
    )

    try:
        one_time_login_url = user.get_one_time_login_url()

        print(
            f"Success getting one time login URL for installation with path '{path}', user with ID '{user.id}'"  # noqa: E501
        )
    except Exception as e:
        # If action fails, don't crash entire program

        print(
            f"Error getting one time login URL for installation with path '{path}', user with ID '{user.id}': {e}"  # noqa: E501
        )

    # Publish message

    channel.basic_publish(
        exchange=method.exchange,
        routing_key=properties.reply_to,
        properties=pika.BasicProperties(
            correlation_id=properties.correlation_id,
            content_type="application/json",
        ),
        body=json.dumps({"one_time_login_url": one_time_login_url}),
    )
