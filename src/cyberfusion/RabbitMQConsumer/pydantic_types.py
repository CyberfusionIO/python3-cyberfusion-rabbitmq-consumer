from pydantic import GetCoreSchemaHandler, AfterValidator
from pydantic_core import CoreSchema, core_schema

import os
from typing import Annotated, Any

LENGTH_PATH_TOTAL_MAX = 4096
LENGTH_PATH_ELEMENT_MAX = 255


def is_valid_path(string: str) -> tuple[bool, str]:
    """Check if given string is a valid path."""
    if len(string) > LENGTH_PATH_TOTAL_MAX:
        return False, f"path must be under {LENGTH_PATH_TOTAL_MAX} characters"

    if any(
        len(element) > LENGTH_PATH_ELEMENT_MAX for element in string.split(os.path.sep)
    ):
        return False, f"path element must be under {LENGTH_PATH_ELEMENT_MAX} characters"

    return True, "path is valid"


def validate_relative_path(value: str) -> str:
    if not value:
        raise ValueError("Value may not be empty")

    if os.path.isabs(value):
        raise ValueError("Path is not relative")

    valid_path, reason = is_valid_path(value)

    if not valid_path:
        raise ValueError(f"Path is not relative: {reason}")

    value = os.path.normpath(value)

    return value


def validate_absolute_path(value: str) -> str:
    if not value:
        raise ValueError("Value may not be empty")

    if not os.path.isabs(value):
        raise ValueError("Path is not absolute")

    valid_path, reason = is_valid_path(value)

    if not valid_path:
        raise ValueError(f"Path is not absolute: {reason}")

    value = os.path.normpath(value)

    return value


class PydanticCompatibleStringType(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        """Return pydantic-core schema.

        This makes the type usable by Pydantic (without `arbitrary_types_allowed`).

        From https://docs.pydantic.dev/latest/concepts/types/#as-a-method-on-a-custom-type
        """
        return core_schema.no_info_after_validator_function(cls, handler(str))


class AbsolutePathType(PydanticCompatibleStringType):
    pass


class RelativePathType(PydanticCompatibleStringType):
    pass


AbsolutePath = Annotated[AbsolutePathType, AfterValidator(validate_absolute_path)]

RelativePath = Annotated[RelativePathType, AfterValidator(validate_relative_path)]
