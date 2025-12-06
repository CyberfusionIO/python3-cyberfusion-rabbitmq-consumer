import requests
import logging
from cyberfusion.Common import get_hostname
from typing import List
from cyberfusion.RabbitMQConsumer.rabbitmq import RabbitMQ
from cyberfusion.RabbitMQConsumer.utilities import join_url_parts
from typing import Optional
from requests.adapters import HTTPAdapter, Retry
from functools import cached_property

logger = logging.getLogger(__name__)


class LogServerClient:
    """Log server client."""

    def __init__(self, base_url: str, api_token: str, rabbitmq: RabbitMQ) -> None:
        """Set attributes."""
        self.base_url = base_url
        self.api_token = api_token
        self.rabbitmq = rabbitmq

    @cached_property
    def session(self) -> requests.sessions.Session:
        """Get requests session with retries."""
        session = requests.Session()

        adapter = HTTPAdapter(
            max_retries=Retry(
                total=5,
                backoff_factor=1,
            )
        )

        session.mount(self.base_url, adapter)

        session.headers.update({"X-API-Token": self.api_token})

        return session

    @staticmethod
    def handle_request(request: requests.models.Response) -> None:
        try:
            request.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.warning(
                "HTTP %s error on %s: %s",
                (e.response.status_code, e.request.url, e.response.text),
            )

        logger.debug("HTTP request on %s succeeded: %s", (request.url, request.text))

    def log_rpc_request(
        self,
        *,
        correlation_id: str,
        request_payload: dict,
        decrypted_values: List[str],
        exchange_name: str,
    ) -> None:
        """Log RPC request."""
        for decrypted_value in decrypted_values:
            request_payload[decrypted_value] = "*****"

        request = self.session.post(
            join_url_parts(self.base_url, "rpc-requests"),
            json={
                "correlation_id": correlation_id,
                "request_payload": request_payload,
                "virtual_host_name": self.rabbitmq.virtual_host_name,
                "queue_name": self.rabbitmq.virtual_host_config.queue,
                "rabbitmq_username": self.rabbitmq.config.server.username,
                "hostname": get_hostname(),
                "exchange_name": exchange_name,
            },
        )

        self.handle_request(request)

    def log_rpc_response(
        self, *, correlation_id: str, response_payload: dict, traceback: Optional[str]
    ) -> None:
        """Log RPC response."""
        request = self.session.post(
            join_url_parts(self.base_url, "rpc-responses"),
            json={
                "correlation_id": correlation_id,
                "response_payload": response_payload,
                "traceback": traceback,
            },
        )

        self.handle_request(request)
