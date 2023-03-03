# python3-cyberfusion-cluster-rabbitmq-consumer

This package provides a RabbitMQ consumer that runs on cluster nodes. The RabbitMQ consumer has methods for messages sent to several exchanges, which allows for implementing RPC.

# Run

The consumer is run by calling `rabbitmq_consume.main`. The environment variable `RABBITMQ_CONSUMER_CONFIG_FILE_PATH` must be set. The config is read from this file. An example config may be found in the `rabbitmq.yml` file in the project root.

# systemd

The package contains a systemd target that allows you to easily run a separate process per virtual host. The virtual host name is set as the first argument to the installed command.

# RPC response contract

Every RPC response contains a JSON document, which contains the following objects. Developers of this package should make sure their handle methods return data as specified here. Clients of the RabbitMQ consumer are guaranteed the response matches this format.

* `success` (boolean, non-nullable). Indicates whether the server-side actions succeeded.
* `data` (free-form dict with key-value pairs with a value of any type, non-nullable). Contains exchange-specific data that is relevant for the client. The key-value pairs in the dict may be found in the docstring of the applicable handle method. When `success` is `false`, keys that are normally included in this dict may be omitted. In general, you should not assume that the data dict contains anything when `success` is `false`.
* `message` (string, nullable). Human-readable free-form message related to the response. This may be `null` when there is nothing to report.

# Handling messages

When receing a message, the consumer calls the `handle` method on `cyberfusion.RabbitMQHandlers.$exchange_name`. In order to avoid putting logic for **all** exchanges in this package, specific packages should add modules for each exchange using [native namespace packages](https://packaging.python.org/en/latest/guides/packaging-namespace-packages/#native-namespace-packages).

When writing handle methods, please keep the following in mind:

* Every handle method MUST BE IDEMPOTENT. Messages WILL be retried, and thus handled again, if the consumer dies before fully processing the message (i.e. not acknowledging it).
* Every exchange module must have a constant called `KEY_IDENTIFIER_EXCLUSIVE`. See the comment in `rabbitmq_consume.callback` for an explanation.

# Setup locally

## Docker Compose

Start:

```bash
docker-compose up
```

Stop:

```bash
docker-compose down
```

## Environment variables for tests

The following environment variables may be passed to the `pytest` command. The variables have sensible defaults, i.e. the ones used by the Docker Compose file and CI.

A config file will be automatically generated based on the values of these environment variables, so do not set `RABBITMQ_CONSUMER_CONFIG_FILE_PATH` manually.

* `RABBITMQ_VIRTUAL_HOST_NAME`. The virtual host will be created by the tests if it does not exist.
* `RABBITMQ_HOST`
* `RABBITMQ_USERNAME`. If the virtual host does not exist, the user must have the administrator tag in order to create it.
* `RABBITMQ_PASSWORD`
* `RABBITMQ_AMQP_PORT`
* `RABBITMQ_MANAGEMENT_PORT`
* `RABBITMQ_SSL`
* `RABBITMQ_FERNET_KEY`
