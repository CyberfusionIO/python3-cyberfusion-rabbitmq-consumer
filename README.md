# python3-cyberfusion-cluster-rabbitmq-consumer

RabbitMQ consumer.

This RabbitMQ consumer receives RPC requests, delegates message processing to a handler, and sends RPC responses.

# Install

## Generic

Run the following command to create a source distribution:

    python3 setup.py sdist

## Start/stop services with Docker Compose

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

Find an example config in `rabbitmq.yml`.

# Usage

## Run

    RABBITMQ_CONSUMER_CONFIG_FILE_PATH=/etc/cyberfusion/rabbitmq.yml /usr/bin/cluster-rabbitmq-consume $VIRTUAL_HOST_NAME

## systemd

The package ships a systemd target. This allows you to run separate RabbitMQ consumer processes for virtual hosts.

Specify the virtual host name as the parameter (after `@`). It is passed to the command above.

### Handlers

When an RPC request is received, processing is delegated to a handler.

The handler is imported from the module `cyberfusion.RabbitMQHandlers` followed by the exchange name.

A class called `Handler` is then called (and therefore must implement `__call__`). It must be a subclass of `cyberfusion.RabbitMQHandlers.contracts.HandlerBase` (Pydantic model).

The `__call__` method must return a subclass of `cyberfusion.RabbitMQHandlers.contracts.RPCResponseBase` (Pydantic model).

To ship (exchange-specific) handler modules in multiple packages, you can use [native namespace packages](https://packaging.python.org/en/latest/guides/packaging-namespace-packages/#native-namespace-packages).

### Idempotency

* Handle methods are idempotent. Messages will be retried if the consumer dies before fully processing them, as they will not be acknowledged.

# Tests

## Manually

Run tests with pytest:

    pytest tests/

Pass the following environment variables:

* `RABBITMQ_VIRTUAL_HOST_NAME`. Created if it doesn't exist.
* `RABBITMQ_HOST`
* `RABBITMQ_USERNAME`. Must have 'administrator' tag.
* `RABBITMQ_PASSWORD`
* `RABBITMQ_AMQP_PORT`
* `RABBITMQ_MANAGEMENT_PORT`
* `RABBITMQ_SSL`
* `RABBITMQ_FERNET_KEY` (optional)

Note:

- The `RABBITMQ_CONSUMER_CONFIG_FILE_PATH` environment variable is ignored.

## With services running with Docker Compose

    RABBITMQ_SSL=false RABBITMQ_VIRTUAL_HOST_NAME=test RABBITMQ_HOST=127.0.0.1 RABBITMQ_USERNAME=test RABBITMQ_PASSWORD='C4P4BZFcaBUYk2PvVyZU7CV3' RABBITMQ_AMQP_PORT=5672 RABBITMQ_MANAGEMENT_PORT=15672 PYTHONPATH=/opt/homebrew/lib/python3.11/site-packages:src/:../python3-cyberfusion-common/python3-cyberfusion-common/src/ pytest
