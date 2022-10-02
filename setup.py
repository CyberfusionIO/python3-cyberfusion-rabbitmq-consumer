"""A setuptools based setup module."""

from setuptools import setup

setup(
    name="python-cyberfusion-cluster-rabbitmq-consumer",
    version="1.8.2.1.1",
    description="RabbitMQConsumer Python library/tools",
    author="William Edwards",
    author_email="wedwards@cyberfusion.nl",
    url="https://vcs.cyberfusion.nl/cyberfusion/python-cyberfusion-cluster-rabbitmq-consumer",
    license="Closed",
    packages=[
        "cyberfusion.RabbitMQConsumer",
        "cyberfusion.RabbitMQHandlers.exchanges.dx_configuration_manager_present",
        "cyberfusion.RabbitMQHandlers.exchanges.dx_service_reload",
        "cyberfusion.RabbitMQHandlers.exchanges.dx_service_restart",
    ],
    package_dir={"": "src"},
    platforms=["linux"],
    data_files=[],
    entry_points={
        "console_scripts": [
            "cf-cluster-rabbitmq-consume=cyberfusion.RabbitMQConsumer.rabbitmq_consume:main",
        ]
    },
)
