# python3-cyberfusion-cluster-rabbitmq-consumer

RabbitMQ consumer for clusters.

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

Find an example configs in `rabbitmq.yml`.

# Usage

## Run

    RABBITMQ_CONSUMER_CONFIG_FILE_PATH=/etc/cyberfusion/rabbitmq.yml /usr/bin/cf-cluster-rabbitmq-consume $VIRTUAL_HOST_NAME

## systemd

The package ships a systemd target. Specify the virtual host name as the parameter (after `@`). It is passed to the command above.

## Developing handle methods

When receiving a message, the consumer calls `cyberfusion.RabbitMQHandlers.$exchange_name.handle`.

### Python namespaces

Multiple packages place exchange-specific modules under `cyberfusion.RabbitMQHandlers` using [native namespace packages](https://packaging.python.org/en/latest/guides/packaging-namespace-packages/#native-namespace-packages).

### RPC response contract

Return JSON with the following objects:

* `success` (boolean, non-nullable)
* `data` (free-form dict with key-value pairs with value of any type, non-nullable)
* - Mention key-value pairs in this object in the docstring.
* - When `success` is `false`, this should be an empty dict.
* `message` (human-readable free-form string, nullable)

### Rules

* Handle methods are idempotent. Messages will be retried if the consumer dies before fully processing them, as they will not be acknowledged.
* Exchange modules have a constant called `KEY_IDENTIFIER_EXCLUSIVE`. See the comment in `rabbitmq_consume.callback` for an explanation.

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
