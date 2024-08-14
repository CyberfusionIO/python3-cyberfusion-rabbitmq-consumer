"""A setuptools based setup module."""

from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="python3-cyberfusion-rabbitmq-consumer",
    version="2.1.1.5.1",
    description="Lean RPC framework based on RabbitMQ.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.11",
    author="William Edwards",
    author_email="wedwards@cyberfusion.nl",
    url="https://github.com/CyberfusionIO/python3-cyberfusion-rabbitmq-consumer",
    packages=[
        "cyberfusion.RabbitMQConsumer",
        "cyberfusion.RabbitMQHandlers.exchanges.dx_example",
    ],
    package_dir={"": "src"},
    platforms=["linux"],
    data_files=[],
    install_requires=[
        "cached_property==1.5.2",
        "cryptography==38.0.4",
        "docopt==0.6.2",
        "pika==1.2.0",
        "pydantic==1.10.4",
        "PyYAML==6.0",
        "schema==0.7.5",
        "sdnotify==0.3.1",
    ],
    entry_points={
        "console_scripts": [
            "rabbitmq-consumer=cyberfusion.RabbitMQConsumer.rabbitmq_consume:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords=["cyberfusion", "rabbitmq", "amqp", "rpc"],
    license="MIT",
)
