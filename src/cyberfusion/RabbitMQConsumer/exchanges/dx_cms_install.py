"""Methods for exchange."""

import logging

import pika

from cyberfusion.ClusterSupport.cmses import CMSSoftwareNames
from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ
from cyberfusion.WordPressSupport import Config as WordPressConfig
from cyberfusion.WordPressSupport import Core as WordPressCore
from cyberfusion.WordPressSupport import Installation as WordPressInstallation

logger = logging.getLogger(__name__)


def handle(
    rabbitmq: RabbitMQ,
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
    json_body: dict,
) -> None:
    """Handle message."""

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

        # Do nothing if already installed

        if core.is_installed:
            logger.info(
                f"Core for CMS on Virtual Host with public root '{public_root}' already installed, doing nothing"
            )

            return

        # Download core

        logger.info(
            f"Downloading core for CMS on Virtual Host with public root '{public_root}'"
        )

        try:
            core.download(version=version, locale=locale)

            logger.info(
                f"Success downloading core for CMS on Virtual Host with public root '{public_root}'"
            )
        except Exception:
            logger.exception(
                f"Error downloading core for CMS on Virtual Host with public root '{public_root}'"
            )

            return

        # Get Config object

        config = WordPressConfig(installation)

        # Create config

        logger.info(
            f"Creating config for CMS on Virtual Host with public root '{public_root}'"
        )

        try:
            config.create(
                database_name=database_name,
                database_username=database_user_name,
                database_user_password=database_user_password,
                database_host=database_host,
            )

            logger.info(
                f"Success creating config for CMS on Virtual Host with public root '{public_root}'"
            )
        except Exception:
            logger.exception(
                f"Error creating config for CMS on Virtual Host with public root '{public_root}'"
            )

            return

        # Install core

        logger.info(
            f"Installing core for CMS on Virtual Host with public root '{public_root}'"
        )

        try:
            core.install(
                url=site_url,
                site_title=site_title,
                admin_username=admin_username,
                admin_password=admin_password,
                admin_email_address=admin_email_address,
            )

            logger.info(
                f"Success installing core for CMS on Virtual Host with public root '{public_root}'"
            )
        except Exception:
            logger.exception(
                f"Error installing core for CMS on Virtual Host with public root '{public_root}'"
            )

            return

        # Done, return

        return

    # When we get here, other software than WordPress: not supported

    logger.info(
        f"Software '{software_name}' for CMS on Virtual Host with public root '{public_root}' not supported, doing nothing"
    )

    return
