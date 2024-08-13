"""Pydantic types for use by handlers."""

from __future__ import annotations

import os
from typing import Generator


class AbsolutePath(str):
    """Custom Pydantic absolute path validator."""

    @classmethod
    def __get_validators__(cls) -> Generator:  # noqa: D105
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> AbsolutePath:  # noqa: D102
        if not isinstance(value, str):
            raise TypeError("Value is not string")

        if not os.path.isabs(value):
            raise ValueError(
                "Value is not valid absolute path. The path must start from the root element."
            )

        return cls(f"{value}")

    def __repr__(self) -> str:  # noqa: D105
        return f"AbsolutePath({super().__repr__()})"


class RelativePath(str):
    """Custom Pydantic relative path validator."""

    @classmethod
    def __get_validators__(cls) -> Generator:  # noqa: D105
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> RelativePath:  # noqa: D102
        if not isinstance(value, str):
            raise TypeError("Value is not string")

        if os.path.isabs(value):
            raise ValueError("Value is not valid relative path")

        return cls(f"{value}")

    def __repr__(self) -> str:  # noqa: D105
        return f"RelativePath({super().__repr__()})"
