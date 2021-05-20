"""Methods for exchange."""

import json

import pika

from cyberfusion.ClusterSupport import ClusterSupport
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

    # Get support object

    support = ClusterSupport()

    # Get API object

    obj = support.get_virtual_hosts(id_=json_body["virtual_host_id"])[0]

    # Get Installation object

    installation = Installation(
        obj.public_root,
        obj.unix_user.unix_id,
        obj.unix_user.unix_id,
        obj.unix_user.virtual_hosts_directory,
    )

    # Get administrator users

    users = Users(installation).get(role=User.NAME_ROLE_ADMINISTRATOR)

    # Pick first user

    user = users[0]

    # Get one time login URL

    print(
        f"Getting one time login URL for CMS on Virtual Host with public root '{obj.public_root}', user with ID '{user.id}'"  # noqa: E501
    )

    try:
        one_time_login_url = user.get_one_time_login_url()

        print(
            f"Success getting one time login URL for CMS on Virtual Host with public root '{obj.public_root}', user with ID '{user.id}'"  # noqa: E501
        )
    except Exception as e:
        # If action fails, don't crash entire program

        print(
            f"Error getting one time login URL for CMS on Virtual Host with public root '{obj.public_root}', user with ID '{user.id}': {e}"  # noqa: E501
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
