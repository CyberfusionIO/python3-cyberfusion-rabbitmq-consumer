"""Methods for exchange."""

import json
import logging

import pika

from cyberfusion.Common.Command import CyberfusionCommand
from cyberfusion.RabbitMQConsumer.exceptions.dx_configuration_manager_present import (
    ConfigurationManagerPresentError,
)
from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ
from cyberfusion.RabbitMQConsumer.utilities import _prefix_message

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
        # Set commands. We decide the commands in the config, so that the commands
        # can be determined by any data source (e.g. Ansible based on Cluster API
        # output), rather than being hardcoded here.
        #
        # Every command has to return JSON. This JSON must contain the objects
        # 'changed', 'unchanged' and 'differences'. These objects must contain dicts with an
        # action as key and a list with objects as value.

        commands = [
            command.split(" ")
            for command in rabbitmq.config["virtual_hosts"][
                rabbitmq.virtual_host_name
            ]["exchanges"][method.exchange]["commands"]
        ]

        # Set preliminary result

        success = True
        result = _prefix_message(None, "Configurations updated")

        # Run commands

        for command in commands:
            split_command = " ".join(command)  # Human-readable for messages

            logger.info(_prefix_message(split_command, "Running..."))

            try:
                # Run command, should return JSON (see comment above)

                output = json.loads(CyberfusionCommand(command).stdout)

                # We want to receive notifications in case of changes. Log level
                # is set to warning, so this takes care of that

                if any(
                    output["changed"].values()
                ):  # If any list in 'changed' is non-empty
                    # Add changed

                    message = f"Changed: {output['changed']}\n"

                    # Add differences

                    for key, differences in output["differences"].items():
                        message += _prefix_message(key, "Differences:\n")

                        for difference in differences:
                            message += _prefix_message(
                                key, f"\t{difference}\n"
                            )

                    # Log message

                    logger.warning(_prefix_message(split_command, message))
                else:
                    logger.info(_prefix_message(split_command, "No changes"))

            except Exception:
                raise ConfigurationManagerPresentError

    except ConfigurationManagerPresentError as e:
        # Set result from error and log exception

        success = False
        result = _prefix_message(None, e.result)

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
