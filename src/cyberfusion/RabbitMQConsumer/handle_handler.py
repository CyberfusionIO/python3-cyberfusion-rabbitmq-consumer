"""Handle RabbitMQ exchange handler. Pass request payload as stdin.

Usage:
  rabbitmq-consumer-handle-handler --exchange-name=<exchange-name> --response-file=<response-file>

Options:
  -h --help                                      Show this screen.
  --exchange-name=<exchange-name>                Exchange name.
  --response-file=<response-file>                File to write response to.
"""

import json
import sys


from docopt import docopt
from schema import Schema
from cyberfusion.RabbitMQConsumer.utilities import (
    get_exchange_handler_class_request_model,
)
import os

importlib_ = __import__("importlib")


def main() -> None:
    args = docopt(__doc__)

    schema = Schema({"--exchange-name": str, "--response-file": str})

    args = schema.validate(args)

    exchange_name = args["--exchange-name"]
    response_file = args["--response-file"]

    import_module = f"cyberfusion.RabbitMQHandlers.exchanges.{exchange_name}"

    module = importlib_.import_module(import_module)

    handler = module.Handler()

    request_payload = json.loads(sys.stdin.read())

    request_model = get_exchange_handler_class_request_model(handler)

    request = request_model(**request_payload)

    response = handler(request)

    # Write output to file, so the handler response isn't mixed with other writes
    # to stdout/stderr (e.g. from systemd)

    with open(response_file, "w") as f:
        os.chmod(response_file, 0o600)

        f.write(json.dumps(response.model_dump(mode="json")))
