"""Generic utilities."""

from urllib.parse import urljoin
import importlib.util
import inspect
import logging
import pkgutil
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
from cyberfusion.RabbitMQHandlers import exchanges

logger = logging.getLogger(__name__)

importlib_ = __import__("importlib")


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
    """Import exchange handler modules specified in config."""
    modules = {}

    for exchange in exchanges:
        import_module = f"cyberfusion.RabbitMQHandlers.exchanges.{exchange.name}"

        try:
            modules[exchange.name] = importlib_.import_module(import_module)
        except ModuleNotFoundError as e:
            if e.name == import_module:
                logger.warning(
                    "Module for exchange '%s' could not be found, skipping...",
                    exchange.name,
                )

                continue

            raise

    return modules


def import_installed_handler_modules() -> List[types.ModuleType]:
    """Import all exchange handler modules installed on system."""
    modules = []

    modules_infos = pkgutil.iter_modules(exchanges.__path__)

    for module_info in modules_infos:
        # Use FileFinder (`module_info.module_finder.find_spec`) instead of
        # `importlib.util.find_spec`, as `path` is already set correctly

        spec = module_info.module_finder.find_spec(module_info.name)  # type: ignore[call-arg]

        # Ignore this module if no spec could be found. AFAIK, this should not
        # be able to happen in normal circumstances, as we're iterating over
        # modules which we know exist (as they were found).

        if not spec:
            continue

        module = importlib.util.module_from_spec(spec)

        if not spec.loader:
            continue

        spec.loader.exec_module(module)

        modules.append(module)

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


def join_url_parts(*args: str) -> str:
    """Join URL parts."""
    result = ""

    for arg in args:
        result = urljoin(result, arg)

        # Prevent part from being replaced:
        #
        # >>> from urllib.parse import urljoin
        # >>> urljoin('http://localhost/certificates', 'request')
        # 'http://localhost/request'
        # >>> urljoin('http://localhost/certificates/', 'request')
        # 'http://localhost/certificates/request'

        if result.endswith("/"):
            continue

        result += "/"

    result = result[: -len("/")]  # Remove trailing slash

    return result
