"""Methods for exchange."""

import json
from typing import Optional

import pika

from cyberfusion.ClusterApiCli import ClusterApiRequest
from cyberfusion.ClusterSupport import ClusterSupport
from cyberfusion.Common.Command import CommandNonZeroError, CyberfusionCommand
from cyberfusion.RabbitMQConsumer.exceptions.command import (
    BinaryNotAllowedError,
)
from cyberfusion.RabbitMQConsumer.RabbitMQ import RabbitMQ


def handle(
    rabbitmq: RabbitMQ,
    channel: pika.adapters.blocking_connection.BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.spec.BasicProperties,
    body: str,
) -> None:
    """Handle message."""  # noqa: D202

    # Cast body

    json_body = json.loads(body)

    # Set variable

    command = json_body["command"]

    # Get support object

    support = ClusterSupport()

    # Get command object

    command_obj = support.get_commands(id_=json_body["command_id"])[0]

    # Check if binary allowed

    try:
        for allowed_binary in rabbitmq.config["virtual_hosts"][
            rabbitmq.virtual_host
        ]["exchanges"][method.exchange]["allowed_binaries"]:
            if command == allowed_binary or command.startswith(
                allowed_binary + " "
            ):
                break

            raise BinaryNotAllowedError
    except BinaryNotAllowedError:
        print("Binary not allowed, not running command")

        return

    # Run command

    print(f"Running command: '{command}'")

    output: Optional[CyberfusionCommand] = None

    try:
        output = CyberfusionCommand(
            command,
            uid=json_body["unix_id"],
            gid=json_body["unix_id"],
            path=json_body["path"],
            environment={
                "PWD": json_body["path"],
                "HOME": json_body["home"],
            },
        )
    except CommandNonZeroError as e:
        print(f"Error running command '{command}': {e}")

        command_obj.return_code = e.rc
        command_obj.standard_out = e.stdout
    except Exception as e:
        print(f"Error running command '{command}': {e}")

        command_obj.return_code = None
        command_obj.standard_out = None

    if output:
        print(f"Success running command: '{command}'")

        command_obj.return_code = output.rc
        command_obj.standard_out = output.stdout

    # Update object

    support.execute_api_call(
        ClusterSupport.ENDPOINT_COMMANDS + "/" + str(json_body["command_id"]),
        method=ClusterApiRequest.METHOD_PUT,
        data={
            "id": command_obj.id,
            "command": command_obj.command,
            "return_code": command_obj.return_code,
            "standard_out": command_obj.standard_out,
            "virtual_host_id": command_obj.virtual_host_id,
            "cluster_id": command_obj.cluster_id,
        },
    )
