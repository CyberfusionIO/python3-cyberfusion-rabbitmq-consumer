"""A setuptools based setup module."""

from setuptools import setup

setup(
    name="python3-cyberfusion-rabbitmq-consumer",
    version="2.0.2.3",
    description="RabbitMQ consumer for RPC.",
    author="William Edwards",
    author_email="wedwards@cyberfusion.nl",
    url="https://vcs.cyberfusion.nl/core/python3-cyberfusion-rabbitmq-consumer",
    license="Closed",
    packages=[
        "cyberfusion.RabbitMQConsumer",
        "cyberfusion.RabbitMQHandlers.exchanges.dx_example",
    ],
    package_dir={"": "src"},
    platforms=["linux"],
    data_files=[],
    entry_points={
        "console_scripts": [
            "rabbitmq-consumer=cyberfusion.RabbitMQConsumer.rabbitmq_consume:main",
        ]
    },
)
