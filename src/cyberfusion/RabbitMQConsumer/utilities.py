"""Generic utilities."""

import inspect
import logging
import ssl
import types
from typing import Dict, List, Optional

import pika

from cyberfusion.RabbitMQConsumer.config import Exchange
from cyberfusion.RabbitMQConsumer.contracts import (
    HandlerBase,
    RPCRequestBase,
    RPCResponseBase,
)

logger = logging.getLogger(__name__)

importlib = __import__("importlib")


def _prefix_message(prefix: Optional[str], result: str) -> str:
    """Add user-specified prefix to message."""
    if prefix:
        return f"[{prefix}] {result}"

    return result


def get_pika_ssl_options(host: str) -> pika.SSLOptions:
    """Get pika.SSLOptions object.

    Used in `pika.ConnectionParameters(ssl_options=...)`.
    """
    return pika.SSLOptions(ssl.create_default_context(), host)


def import_exchange_handler_modules(
    exchanges: List[Exchange],
) -> Dict[str, types.ModuleType]:
    """Import exchange handler modules."""
    modules = {}

    for exchange in exchanges:
        import_module = (
            f"cyberfusion.RabbitMQHandlers.exchanges.{exchange.name}"
        )

        try:
            modules[exchange.name] = importlib.import_module(import_module)
        except ModuleNotFoundError as e:
            if e.name == import_module:
                logger.warning(
                    "Module for exchange '%s' could not be found, skipping...",
                    exchange.name,
                )

                continue

            raise

    return modules


def get_exchange_handler_class_request_model(
    handler: HandlerBase,
) -> RPCRequestBase:
    """Get exchange handler request model by introspection."""
    return inspect.signature(handler.__call__).parameters["request"].annotation


def get_exchange_handler_class_response_model(
    handler: HandlerBase,
) -> RPCResponseBase:
    """Get exchange handler response model by introspection."""
    return inspect.signature(handler.__call__).return_annotation
