"""Methods for exchange."""

import json
import logging

import pika

from cyberfusion.RabbitMQConsumer.exceptions.dx_cms_install import (
    CMSInstalledError,
    CMSInstallError,
    WordPressConfigCreateError,
    WordPressCoreDownloadError,
    WordPressCoreInstallError,
)
from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ
from cyberfusion.RabbitMQConsumer.utilities import _prefix_message
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
    try:
        # Set variables

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

        # Set preliminary result

        success = True
        result = _prefix_message(public_root, "CMS installed")

        # Get installation

        installation = WordPressInstallation(
            public_root,
            working_directory,
        )

        # Download core

        core = WordPressCore(installation)

        if core.is_installed:
            raise CMSInstalledError

        logger.info(_prefix_message(public_root, "Downloading core"))

        try:
            core.download(version=version, locale=locale)
        except Exception:
            raise WordPressCoreDownloadError

        # Create config

        logger.info(_prefix_message(public_root, "Creating config"))

        config = WordPressConfig(installation)

        try:
            config.create(
                database_name=database_name,
                database_username=database_user_name,
                database_user_password=database_user_password,
                database_host=database_host,
            )
        except Exception:
            raise WordPressConfigCreateError

        # Install core

        logger.info(_prefix_message(public_root, "Install core"))

        try:
            core.install(
                url=site_url,
                site_title=site_title,
                admin_username=admin_username,
                admin_password=admin_password,
                admin_email_address=admin_email_address,
            )
        except Exception:
            raise WordPressCoreInstallError

    except CMSInstallError as e:
        # Set result from error and log exception

        success = False
        result = _prefix_message(public_root, e.result)

        logger.exception(result)

    # Publish result

    channel.basic_publish(
        exchange=method.exchange,
        routing_key=properties.reply_to,
        properties=pika.BasicProperties(
            correlation_id=properties.correlation_id,
            content_type="application/json",
        ),
        body=json.dumps({"success": success, "message": result}),
    )
