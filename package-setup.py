from setuptools import setup

setup(
    name="python-cyberfusion-cluster-rabbitmq-consumer",
    version="1.0",
    description="Program for RabbitMQ consumers",
    author="William Edwards",
    author_email="wedwards@cyberfusion.nl",
    url="https://vcs.cyberfusion.nl/cyberfusion/python-cyberfusion-cluster-rabbitmq-consumer",  # noqa: E501
    license="Closed",
    packages=[
        "cyberfusion.RabbitMQConsumer",
        "cyberfusion.RabbitMQConsumer.exchanges",
        "cyberfusion.RabbitMQConsumer.exceptions",
    ],
    package_dir={"": "src"},
    platforms=["linux"],
    data_files=[],
    entry_points={
        "console_scripts": [
            "cf-cluster-rabbitmq-consume=cyberfusion.RabbitMQConsumer.rabbitmq_consume:main",  # noqa: E501
        ]
    },
)
