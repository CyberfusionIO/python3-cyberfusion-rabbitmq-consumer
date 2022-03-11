# python-cyberfusion-cluster-rabbitmq-consumer

This package provides a RabbitMQ consumer that runs on cluster nodes. The RabbitMQ consumer has methods for messages sent to several exchanges, which allows for implementing RPC.

# systemd

The package contains a systemd target that allows you to easily run a separate process per virtual host. The virtual host name is set as the first arugment to the installed command.

# RPC response contract

Every RPC response contains a JSON document, which contains the following objects. Developers of this package should make sure their handle methods return data as specified here. Clients of the RabbitMQ consumer are guaranteed the response matches this format.

* `success` (boolean, non-nullable). Indicates whether the server-side actions succeeded.
* `data` (free-form dict with key-value pairs with a value of any type, non-nullable). Contains exchange-specific data that is relevant for the client. The key-value pairs in the dict may be found in the docstring of the applicable handle method. When `success` is `false`, keys that are normally included in this dict may be omitted. In general, you should not assume the data dict to contain anything when `success` is `false`.
* `message` (string, nullable). Human-readable free-form message related to the response. This may be `null` when there is nothing to report.
