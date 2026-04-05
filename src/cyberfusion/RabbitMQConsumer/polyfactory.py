from typing import Dict, Generic, Type, TypeVar, Any

from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.field_meta import FieldMeta
from cyberfusion.RabbitMQConsumer.contracts import RPCResponseBase
from cyberfusion.RabbitMQConsumer.pydantic_types import (
    AbsolutePathType,
    RelativePathType,
)

T = TypeVar("T", bound=RPCResponseBase)


class PydanticFactory(Generic[T], ModelFactory[T]):
    __is_base_factory__ = True

    success = True

    @classmethod
    def should_set_none_value(cls, field_meta: FieldMeta) -> bool:
        if field_meta.name == "data":
            return False

        return super().should_set_none_value(field_meta)

    @classmethod
    def get_provider_map(cls) -> Dict[Type, Any]:
        providers_map = super().get_provider_map()

        return {
            AbsolutePathType: lambda: cls.__faker__.file_path(
                absolute=True, extension=""
            ),
            RelativePathType: lambda: cls.__faker__.file_path(
                absolute=False, extension=""
            ),
            **providers_map,
        }
