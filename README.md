# python3-cyberfusion-rabbitmq-consumer

Lean RPC framework based on [RabbitMQ](https://www.rabbitmq.com/).

# Features

* Request and response validation (using [Pydantic](https://docs.pydantic.dev/latest/)).
* Auto-generated documentation (using the standalone [documentation server](https://github.com/CyberfusionIO/python3-cyberfusion-rabbitmq-consumer-documentation-server)).
* Strong request-response contract (see '[Pydantic model generation](https://github.com/CyberfusionIO/python3-cyberfusion-rabbitmq-consumer-documentation-server/tree/main?tab=readme-ov-file#pydantic-model-generation)').
* Process multiple RPC requests simultaneously (using threading).
* Encryption (using [Fernet](https://cryptography.io/en/latest/fernet/)).
* Dynamic structure using namespace packaging (see '[Namespace packaging: shipping handlers from multiple packages](#namespace-packaging-shipping-handlers-from-multiple-packages)'.
* Locking.
* Idempotency.
* * RPC requests are retried if anything happens before they are fully processed (as the AMQP message wouldn't be acknowledged).

# Project origins and use case

## A lean RPC framework: why?

Commonly used RPC frameworks include:

* [gRPC](https://grpc.io/)
* [Apache Thrift](https://thrift.apache.org/)

These frameworks do everything you'll ever need. **So why build another framework?**

Exactly *because* other frameworks do almost everything. Our systems must be 1) lean and 2) manageable. The aforementioned frameworks are not.

Finally, consider how 'simple' many use cases are:

* Do RPC request.
* Validate request (syntactic).
* Delegate response generation.
* Return response.

... and building a new, lean RPC framework becomes obvious.

The RPC framework is based on RabbitMQ, because it provides all primitives needed for stable and scalable inter-systems messaging.

## RPC vs REST

Traditionally, REST is the go-to framework for strong-contracted data exchange.

REST is *resource-oriented*: callers operate on resources. For example, one could call the endpoint `GET /fruits/orange/1000` - retrieving orange 1000.

In distributed systems that implement [separation of concerns](https://en.wikipedia.org/wiki/Separation_of_concerns), microservices are *action-oriented*.

Such microservices don't store local objects (such as 'orange 1'). Instead, they execute requests, tied to a specific action.

Using REST in a non-resource-oriented way leads to awkward constructs. **That's where RPC comes in.**

### Example for comparison

An example to clarify the difference between REST and RPC: **update an orange to not have a pith**.

#### REST request

    PATCH /fruits/orange/1000
    {"has_pith": false}

Note:

* The action is indicated using the HTTP method verb (`DELETE`).
* The object is identified using its ID (1000).
* Only the property to update is specified. The REST API has stored the object, and its properties.

#### RPC request

    update_fruit_pith
    {"type": "orange", "location": "Basement", "has_pith": false}

Note:

* The action is explicitly mentioned (`update_fruit_pith`).
* The object is not identified. After all, there is no object to speak of (refer to 'RPC vs REST'), so...
* all object properties are specified (on every request).

# Processing RPC requests

For exchanges and virtual hosts specified in the config file, the RabbitMQ consumer processes RPC requests.

## Handlers are per-exchange

When receiving an RPC request, the exchange-specific *handler* is called, which processes the request.

**Exchanges correspond to actions.** For example, the exchange `dx_delete_server` is expected to *delete a server*.

As deleting a server requires different processing than, for example, creating a server, every exchange has its own *handler*.

The handler returns the RPC response.

## Example

Find a handler example in [`exchanges/dx_example`](src/cyberfusion/RabbitMQHandlers/exchanges/dx_example/__init__.py).

## Where handlers come from

A class called `Handler` is imported from the module `cyberfusion.RabbitMQHandlers.exchanges`, followed by the exchange name. For example: `cyberfusion.RabbitMQHandlers.exchanges.dx_delete_server.Handler`.

The `Handler` class is then called. Therefore, it must implement `__call__`.

A module must exist for every handler. Otherwise, RPC requests for the exchange can't be processed.

## Type annotations and Pydantic: how request and response data is validated

Handlers use Python *type annotations* to indicate the request model (that they expect as input) and response model (that they return).
These models are [Pydantic](https://docs.pydantic.dev/latest/) models, inheriting `RPCRequestBase` and `RPCResponseBase` respectively.

For example:

```python
from typing import Optional

from cyberfusion.RabbitMQConsumer.contracts import (
    RPCRequestBase,
    RPCResponseBase,
    RPCResponseData,
)

class RPCRequestExample(RPCRequestBase):
    ...

class RPCResponseDataExample(RPCResponseData):
    ...

class RPCResponseExample(RPCResponseBase):
    data: Optional[RPCResponseDataExample]

def __call__(
        self,
        request: RPCRequestExample  # Request model
) -> RPCResponseExample:  # Response model
    ...
```

## Strong-contracted (definitions)

A common concept in RPC is 'definitions': using the same response/request models on the client *and* server sides.
As opposed to 'dumb' JSON, using models guarantees that requests and responses are syntactically correct.
This brings many advantages of local calls, such as type validation, to RPC (remote calls).

The RabbitMQ standalone [documentation server](https://github.com/CyberfusionIO/python3-cyberfusion-rabbitmq-consumer-documentation-server) can generate Pydantic models for exchange request/request models, which you can use on the client.
For more information, see '[Pydantic model generation](https://github.com/CyberfusionIO/python3-cyberfusion-rabbitmq-consumer-documentation-server?tab=readme-ov-file#pydantic-model-generation)' in its README.

## Encryption using Fernet

Request data can be encrypted using Fernet.
You encrypt it before publishing the RPC request. The RabbitMQ consumer then decrypts it.
This requires the Fernet key to be known on both ends.

### Example

```python
from cryptography.fernet import Fernet

# Create the key (usually done one-time). Add the key to the RabbitMQ consumer
# config (`fernet_key` under virtual host).

key = Fernet.generate_key().decode()

# Encrypt password

plain_password = 'test'
encrypted_password = Fernet(key).encrypt(
    # Fernet can only encode bytes
    plain_password.encode()
).decode()

rpc_request_payload = {"password": encrypted_password}
```

### Properties

If the request body contains any of the following properties, they must be encrypted:

* `secret_values`
* `passphrase`
* `password`
* `admin_password`
* `database_user_password`

## Namespace packaging: shipping handlers from multiple packages

In some cases, you might want to ship handlers from multiple packages.

For example, if a single RabbitMQ consumer's config contains the following exchanges:

* `dx_create_server` (concerns servers)
* `dx_update_server` (concerns servers)
* `dx_delete_server` (concerns servers)
* `dx_restart_server` (concerns servers)
* `dx_create_tree` (concerns trees)
* `dx_cut_down_tree` (concerns trees)

... you might want two separate packages:

* `RabbitMQHandlersServers` (contains server exchanges)
* `RabbitMQHandlersTrees` (contains tree exchanges)

You can do this using [namespace packaging](https://packaging.python.org/en/latest/guides/packaging-namespace-packages/#native-namespace-packages).
This lets you install the exchange modules above, from multiple packages, into a single module (`cyberfusion.RabbitMQHandlers.exchanges` - where all exchange handlers are imported from, see '[Where handlers come from](#where-handlers-come-from)').

Using namespace packaging is simple: don't add an `__init__.py` to the `exchanges` directory.

To demonstrate, a 'regular' module tree contains `__init__.py` files:

    server_handlers/
        src/
            cyberfusion/
                RabbitMQHandlers/
                    __init__.py
                    exchanges/
                        __init__.py
                        dx_create_server/
                            __init__.py

... while a namespace-packaged tree doesn't:

    server_handlers/
        src/
            cyberfusion/
                RabbitMQHandlers/
                    exchanges/
                        dx_create_server/
                            __init__.py

You can then ship submodules from another package, of which the tree may look like this:

    tree_handlers/
        src/
            cyberfusion/
                RabbitMQHandlers/
                    exchanges/
                        dx_create_tree/
                            __init__.py

## Locking

To prevent conflicting RPC requests from running simultaneously, use `Handler.lock_attribute`.
If multiple RPC requests come in, for which the lock attribute's value is identical, only one is processed at a time.

### Example

Scenario:

* You have an exchange, `dx_upgrade_server`. It should not be possible to upgrade a given server multiple times, simultaneously.
* The exchange's request model has the property `name`.
* On `dx_upgrade_server`, an RPC request with `name = example`, and an RPC request with `name = demonstration` may run simultaneously (because `example` differs from `demonstration`).
* On `dx_upgrade_server`, an RPC request with `name = example`, and another RPC request with `name = example` (identical) may NOT run simultaneously (because `example` is the same as `example`).

Code:

```python
from cyberfusion.RabbitMQConsumer.contracts import HandlerBase

class Handler(HandlerBase):
    ...

    @property
    def lock_attribute(self) -> str:
        return "name"
```

# Executing RPC requests

RPC requests can be made by any caller that speaks AMQP.

See supported client libraries in the [RabbitMQ documentation](https://www.rabbitmq.com/client-libraries).

## Python example with Pika

For Python, Pika is the go-to RabbitMQ/AMQP library.

Below is an example implementation to execute RPC calls (to [`dx_example`](src/cyberfusion/RabbitMQHandlers/exchanges/dx_example/__init__.py). The example corresponds to the config example [`rabbitmq.yml`](rabbitmq.yml).
(As opposed to [RabbitMQ's own example](https://github.com/rabbitmq/rabbitmq-tutorials/blob/main/python/rpc_client.py), the example below implements exception handling, timeouts and SSL.)

```python
import json
import ssl
import uuid
from typing import Any

import pika

from cryptography.fernet import Fernet


class AMQP:
    """A class that allows us to interact with AMQP, usable as a context manager."""

    def __init__(
        self,
        ssl_enabled: bool,
        port: int,
        host: str,
        username: str,
        password: str,
        virtual_host_name: str,
    ) -> None:
        self.ssl_enabled = ssl_enabled
        self.port = port
        self.host = host
        self.username = username
        self.password = password
        self.virtual_host_name = virtual_host_name

        self.set_ssl_options()
        self.set_connection()
        self.set_channel()

    def set_ssl_options(self) -> None:
        self.ssl_options: pika.SSLOptions | None = None

        if self.ssl_enabled:
            self.ssl_options = pika.SSLOptions(
                ssl.create_default_context(), self.host
            )

    def get_credentials(self) -> pika.credentials.PlainCredentials:
        return pika.credentials.PlainCredentials(self.username, self.password)

    def set_connection(self) -> None:
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                virtual_host=self.virtual_host_name,
                credentials=self.get_credentials(),
                ssl_options=self.ssl_options,
            )
        )

    def set_channel(self) -> None:
        self.channel = self.connection.channel()

    def publish(
        self,
        exchange_name: str,
        exchange_type: str,
        routing_key: str,
        *,
        body: dict[str, Any],
    ) -> None:
        self.channel.exchange_declare(
            exchange=exchange_name, exchange_type=exchange_type
        )

        self.channel.basic_publish(
            exchange=exchange_name,
            body=json.dumps(body),
            properties=pika.BasicProperties(
                content_type="application/json",
                # Persistency, so messages don't get lost. For more information, see:
                # https://www.rabbitmq.com/docs/persistence-conf
                delivery_mode=2,
            ),
            routing_key=routing_key,
        )

    def __enter__(self) -> pika.adapters.blocking_connection.BlockingChannel:
        """Return AMQP channel."""
        return self.channel

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[no-untyped-def]
        """Close AMQP connection."""
        self.connection.close()


class RPC:
    """AMQP RPC client."""

    DEFAULT_TIMEOUT = 5 * 60

    def __init__(
        self,
        pika: AMQP,
        queue: str,
        exchange: str,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.pika = pika
        self.routing_key = queue
        self.exchange = exchange
        self.timeout = timeout

        # Set channel, queue, and bind

        self.channel = self.pika.connection.channel()

        self.callback_queue = self.channel.queue_declare(
            queue="", exclusive=True
        ).method.queue

        self.channel.queue_bind(exchange=exchange, queue=self.callback_queue)

        # Set timeout

        self.pika.connection.call_later(timeout, self.timeout_routine)

        # Start consuming

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.callback,
            auto_ack=True,
        )

    def timeout_routine(self) -> None:
        raise Exception(f"RPC call timed out on exchange '{self.exchange}'")

    def publish(self, *, body: dict[str, Any]) -> bytes:
        """Publish message and wait for response."""
        self.response: str | bytes | None = None
        self.correlation_id: str = str(uuid.uuid4())

        self.channel.basic_publish(
            exchange=self.exchange,
            body=json.dumps(body),
            properties=pika.BasicProperties(
                content_type="application/json",
                reply_to=self.callback_queue,
                correlation_id=self.correlation_id,
                #
                # $TIMEOUT can be reached in two cases:
                #
                # - When the message isn't acked in $TIMEOUT, e.g. because the
                #   consumer is offline
                # - When the message processing takes $TIMEOUT
                #
                # In either case, an exception is raised in the 'timeout' method.
                # When this happens because of case #1 (message not acked), we want
                # to ensure that the RPC message does not start processing when the
                # consumer is able to process the message. Therefore, the RPC message
                # should expire after $TIMEOUT; this ensures that, once we've returned
                # the definitive state by raising an exception in the 'timeout' method,
                # the RPC call will not process in the background anyway.
                #
                expiration=str(self.timeout * 1000),
            ),
            routing_key=self.routing_key,
        )

        while self.response is None:
            self.pika.connection.process_data_events()

        # Exception handling and return response

        response = json.loads(self.response)

        if not response["success"]:  # Always present, see `cyberfusion.RabbitMQConsumer.contracts.RPCResponseBase`
            raise Exception("RPC call failed: " + response["message"])

        return self.response

    def callback(
        self,
        channel: pika.adapters.blocking_connection.BlockingChannel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        body: bytes,
    ) -> None:
        """Handle response."""
        if self.correlation_id == properties.correlation_id:
            self.response = body


with AMQP(
    virtual_host_name="test",
    password="password",
    username="username",
    host="host",
    port=5671,
    ssl_enabled=True
) as amqp:
    EXCHANGE = "dx_example"

    amqp.exchange_declare(
        exchange=EXCHANGE,
        exchange_type="direct",
    )

    rpc_client = RPC(
        amqp,
        queue="test",
        exchange=EXCHANGE
    )

    key = Fernet.generate_key().decode()

    response = json.loads(
        rpc_client.publish(
            body={
                "favourite_food": "onion",
                "chance_percentage": Fernet(key).encrypt(b"secret").decode(),
            }
        )
    )


tolerable = response["data"]["tolerable"]
```

# Install

## PyPI

Run the following command to install the package from PyPI:

    pip3 install python3-cyberfusion-rabbitmq-consumer

## Generic

Run the following command to create a source distribution:

    python3 setup.py sdist

## Start/stop services with Docker Compose (development)

Start:

```bash
docker-compose up
```

Stop:

```bash
docker-compose down
```

The following services are started:

* RabbitMQ: `localhost:5672`, `localhost:15672`

## Debian

Run the following commands to build a Debian package:

    mk-build-deps -i -t 'apt -o Debug::pkgProblemResolver=yes --no-install-recommends -y'
    dpkg-buildpackage -us -uc

# Configure

## Sections

The config file contains:

* RabbitMQ server details
* [Virtual hosts](https://www.rabbitmq.com/docs/vhosts)
* Per virtual host: exchanges (see '[Handlers are per-exchange](#handlers-are-per-exchange)')

## Example

Find an example config in [`rabbitmq.yml`](rabbitmq.yml).

# Run

## On Debian with systemd

The Debian package ships a systemd target. This allows you to run separate RabbitMQ consumer processes for every virtual host.

For example, if your config contains the virtual hosts `trees` and `servers`, run:

    systemctl start rabbitmq-consume@trees.service
    systemctl start rabbitmq-consume@servers.service

### Monitoring

To check if all systemd services are running, run:

    /usr/bin/rabbitmq-consumer-status

If any service is inactive, the script exits with a non-zero RC.

### Config file

#### Default

By default, the config file `/etc/cyberfusion/rabbitmq.yml` is used.

#### Customise

To use a different config file, override `CONFIG_FILE_PATH` (using a drop-in file). For example:

```bash
$ cat /etc/systemd/system/rabbitmq-consume@trees.service.d/99-config-file-path.conf
[Service]
Environment=CONFIG_FILE_PATH=/tmp/rabbitmq.yml
```

#### Directory

Non-default configs can be stored in `/etc/cyberfusion/rabbitmq`. This directory is automatically created.

## Manually

    /usr/bin/rabbitmq-consumer --virtual-host-name=<virtual-host-name> --config-file-path=<config-file-path>

The given virtual host must be present in the config.

# Tests

Run tests with pytest:

    pytest tests/
