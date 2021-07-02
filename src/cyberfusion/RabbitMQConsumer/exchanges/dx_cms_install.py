"""Methods for exchange."""

import pika

from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ
from cyberfusion.WordPressSupport import Config as WordPressConfig
from cyberfusion.WordPressSupport import Core as WordPressCore
from cyberfusion.WordPressSupport import Installation as WordPressInstallation


class CMSSoftwareNames:
    WP = "WordPress"


def handle(
    rabbitmq: RabbitMQ,
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
    json_body: dict,
) -> None:
    """Handle message."""  # noqa: D202

    # Set variables

    software_name = json_body["software_name"]
    public_root = json_body["public_root"]
    working_directory = json_body["working_directory"]
    database_name = json_body["database_name"]
    database_user_name = json_body["database_user_name"]
    database_user_password = json_body["database_user_password"]
    database_host = json_body["database_host"]
    site_url = json_body["site_url"]
    locale = json_body["locale"]
    version = json_body["version"]
    site_title = json_body["site_title"]
    admin_username = json_body["admin_username"]
    admin_password = json_body["admin_password"]
    admin_email_address = json_body["admin_email_address"]

    # Handle WordPress CMS install

    if software_name == CMSSoftwareNames.WP:
        # Get Installation object

        installation = WordPressInstallation(
            public_root,
            working_directory,
        )

        # Get Core object

        core = WordPressCore(installation)

        # Download core

        core.download(version=version, locale=locale)

        # Get Config object

        config = WordPressConfig(installation)

        # Create config

        print(
            f"Creating config for CMS on Virtual Host with public root '{public_root}'"  # noqa: E501
        )

        try:
            config.create(
                database_name=database_name,
                database_username=database_user_name,
                database_user_password=database_user_password,
                database_host=database_host,
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
                url=site_url,
                site_title=site_title,
                admin_username=admin_username,
                admin_password=admin_password,
                admin_email_address=admin_email_address,
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
