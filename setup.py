"""A setuptools based setup module."""

from setuptools import setup

setup(
    name="python3-cyberfusion-cluster-rabbitmq-consumer",
    version="1.8.5.3",
    description="RabbitMQ consumer for clusters.",
    author="William Edwards",
    author_email="wedwards@cyberfusion.nl",
    url="https://vcs.cyberfusion.nl/core/python3-cyberfusion-cluster-rabbitmq-consumer",
    license="Closed",
    packages=[
        "cyberfusion.RabbitMQConsumer",
    ],
    package_dir={"": "src"},
    platforms=["linux"],
    data_files=[],
    entry_points={
        "console_scripts": [
            "cluster-rabbitmq-consume=cyberfusion.RabbitMQConsumer.rabbitmq_consume:main",
        ]
    },
)
