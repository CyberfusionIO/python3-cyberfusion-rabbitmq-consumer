# python3-cyberfusion-rabbitmq-consumer

Lean RPC framework based on [RabbitMQ](https://www.rabbitmq.com/).

# Features

* Request and response validation (using [Pydantic](https://docs.pydantic.dev/latest/)).
* Auto-generated documentation (using the standalone [documentation server](https://github.com/CyberfusionIO/python3-cyberfusion-rabbitmq-consumer-documentation-server)).
* Central logging (using the standalone [log server](https://github.com/CyberfusionIO/python3-cyberfusion-rabbitmq-consumer-log-server)).
* Strong request-response contract (see '[Pydantic model generation](https://github.com/CyberfusionIO/python3-cyberfusion-rabbitmq-consumer-documentation-server/tree/main?tab=readme-ov-file#pydantic-model-generation)').
* Process multiple RPC requests simultaneously (using threading).
* Encryption (using [Fernet](https://cryptography.io/en/latest/fernet/)).
* Dynamic structure using namespace packaging (see '[Namespace packaging: shipping handlers from multiple packages](#namespace-packaging-shipping-handlers-from-multiple-packages)'.
* Locking.
* Idempotency.
  * RPC requests are retried if anything happens before they are fully processed (as the AMQP message wouldn't be acknowledged).

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

## Central logging

Use the log server to see all RPC requests/responses - in a single web GUI.

First, set up the log server using its [README](https://github.com/CyberfusionIO/python3-cyberfusion-rabbitmq-consumer-log-server/blob/main/README.md).

Then, configure your RabbitMQ consumer to ship logs to the log server. To the [config file](#config-file), add the following stanza:

```yaml
log_server:
  base_url: https://rabbitmq-log-server.example.com/api/v1/  # Replace by the URL of the log server
  api_token: foobar  # Replace by the API token configured on the log server
```

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

## Restarting

When the RabbitMQ consumer is installed as a Debian package, changes to exchanges trigger a restart of all consumer processes.

If you ship your exchanges as a Debian package, and need files outside of the `RabbitMQHandlers` directory to trigger a restart of all consumer processes, use the `rabbitmq-consumer-restart` trigger. For example:

    $ cat debian/python3-cyberfusion-cluster-configuration-manager.triggers
    activate-await rabbitmq-consumer-restart

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

When the RabbitMQ consumer runs, it will handle RPC requests.
Those RPC requests must be done by a client.

Using Python? Use our [Python-based RPC client](https://github.com/CyberfusionIO/python3-cyberfusion-rpc-client).

Other supported client libraries can be found in the [RabbitMQ documentation](https://www.rabbitmq.com/client-libraries).

# Install

## PyPI

Run the following command to install the package from PyPI:

    pip3 install python3-cyberfusion-rabbitmq-consumer

## Debian

Run the following commands to build a Debian package:

    mk-build-deps -i -t 'apt -o Debug::pkgProblemResolver=yes --no-install-recommends -y'
    dpkg-buildpackage -us -uc

# Configure

## Sections

The config file contains:

* RabbitMQ server details
* (Optional) Log server details; see '[Central logging](#central-logging)'
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

To check if all systemd services are working, run:

    /usr/bin/rabbitmq-consumer-status

If any service is failed, the script exits with a non-zero RC.

### Development

To run the RabbitMQ consumer for development, start the 'RabbitMQ Consumer' PyCharm run configuration.

To publish, run the 'Publisher' PyCharm run configuration (or `publisher.py`). This script publishes a test RPC request to the first virtual host and exchange in `rabbitmq.yml`.

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
