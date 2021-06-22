"""Methods for exchange."""

import pika

from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ
from cyberfusion.WordPressSupport import Config, Core, Installation


def handle(
    rabbitmq: RabbitMQ,
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
    json_body: dict,
) -> None:
    """Handle message."""  # noqa: D202

    # Set variables

    public_root = json_body["public_root"]
    virtual_hosts_directory = json_body["virtual_hosts_directory"]

    # Get Installation object

    installation = Installation(
        public_root,
        virtual_hosts_directory,
    )

    # Get core

    core = Core(installation)

    # Download core

    print(
        f"Downloading core for CMS on Virtual Host with public root '{public_root}'"  # noqa: E501
    )

    try:
        core.download(version=json_body["version"], locale=json_body["locale"])

        print(
            f"Success downloading core for CMS on Virtual Host with public root '{public_root}'"  # noqa: E501
        )
    except Exception as e:
        # If action fails, don't crash entire program

        print(
            f"Error downloading core for CMS on Virtual Host with public root '{public_root}': {e}"  # noqa: E501
        )

        return

    # Get config

    config = Config(installation)

    # Create config

    print(
        f"Creating config for CMS on Virtual Host with public root '{public_root}'"  # noqa: E501
    )

    try:
        config.create(
            database_name=json_body["database_username"],
            database_username=json_body["database_username"],
            database_user_password=json_body["database_user_password"],
            database_host=json_body["database_host"],
        )

        print(
            f"Success creating config for CMS on Virtual Host with public root '{public_root}'"  # noqa: E501
        )
    except Exception as e:
        # If action fails, don't crash entire program

        print(
            f"Error creating config for CMS on Virtual Host with public root '{public_root}': {e}"  # noqa: E501
        )

        return

    # Install core

    print(
        f"Installing core for CMS on Virtual Host with public root '{public_root}'"  # noqa: E501
    )

    try:
        core.install(
            url=json_body["site_url"],
            site_title=json_body["site_title"],
            admin_username=json_body["admin_username"],
            admin_password=json_body["admin_password"],
            admin_email_address=json_body["admin_email_address"],
        )

        print(
            f"Success installing core for CMS on Virtual Host with public root '{public_root}'"  # noqa: E501
        )
    except Exception as e:
        # If action fails, don't crash entire program

        print(
            f"Error installing core for CMS on Virtual Host with public root '{public_root}': {e}"  # noqa: E501
        )

        return
