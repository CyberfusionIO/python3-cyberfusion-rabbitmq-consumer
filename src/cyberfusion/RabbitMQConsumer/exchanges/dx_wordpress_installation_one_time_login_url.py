"""Methods for exchange."""

import json
import logging

import pika

from cyberfusion.RabbitMQConsumer.exceptions.dx_wordpress_installation_one_time_login_url import (
    WordPressOneTimeLoginURLError,
)
from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ
from cyberfusion.RabbitMQConsumer.utilities import _prefix_message
from cyberfusion.WordPressSupport import Installation
from cyberfusion.WordPressSupport.users import User, Users

logger = logging.getLogger(__name__)


def handle(
    rabbitmq: RabbitMQ,
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
    json_body: dict,
) -> None:
    """Handle message.

    data contains:
        - one_time_login_url (string). Omitted when 'success' is false.
    """
    try:
        # Set variables

        public_root = json_body["public_root"]
        virtual_hosts_directory = json_body["virtual_hosts_directory"]

        # Set preliminary result

        one_time_login_url = None

        # Get installation object

        installation = Installation(
            public_root,
            virtual_hosts_directory,
        )

        # Get administrator users

        users = Users(installation).get(role=User.NAME_ROLE_ADMINISTRATOR)

        # Pick first user

        user = users[0]

        # Get one time login URL

        logger.info(
            _prefix_message(
                public_root,
                _prefix_message(user.id, "Getting one time login URL"),
            )
        )

        try:
            one_time_login_url = user.get_one_time_login_url()
        except Exception:
            raise WordPressOneTimeLoginURLError

    except Exception as e:
        # Log exception

        result = _prefix_message(
            public_root,
            e.result
            if isinstance(e, WordPressOneTimeLoginURLError)
            else "An unexpected exception occurred",
        )

        logger.exception(result)

    # Publish message

    channel.basic_publish(
        exchange=method.exchange,
        routing_key=properties.reply_to,
        properties=pika.BasicProperties(
            correlation_id=properties.correlation_id,
            content_type="application/json",
        ),
        body=json.dumps(
            {
                "success": one_time_login_url
                is not None,  # If still None, something went wrong
                "message": None,
                "data": {"one_time_login_url": one_time_login_url}
                if one_time_login_url
                is not None  # Don't include if no success
                else {},
            }
        ),
    )
