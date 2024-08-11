"""Generic utilities."""

import ssl
from typing import Optional

import pika


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
