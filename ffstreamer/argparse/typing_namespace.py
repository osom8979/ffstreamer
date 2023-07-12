# -*- coding: utf-8 -*-

from argparse import Namespace
from typing import (
    Any,
    Final,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from ffstreamer.types.string.to_boolean import string_to_boolean

_T = TypeVar("_T")
AnyNamespace = TypeVar("AnyNamespace", bound=Namespace)

VALUE_SEPARATOR: Final[str] = ":"


def is_optional_hint(hint: Any) -> bool:
    return get_origin(hint) == Union and type(None) in get_args(hint)


def cast_value(hint: Any, value: Any) -> Any:
    assert isinstance(hint, type)
    if issubclass(hint, bool) and isinstance(value, str):
        return string_to_boolean(value)
    else:
        return hint(value)


def str_as_hint(value: str, hint: Any, separator=VALUE_SEPARATOR) -> Any:
    origin = get_origin(hint)
    if origin is None:
        return cast_value(hint, value)

    if origin == Union:
        # Optional[_T] == Union[_T, NoneType]
        args = list(get_args(hint))
        try:
            args.remove(type(None))  # Strip NoneType if it exists
        except ValueError:
            pass
        if len(args) >= 2:
            raise TypeError(f"Ambiguous origin type: {hint}")
        real_type = args[0]
        if isinstance(real_type, type):
            return cast_value(real_type, value)  # e.g. Optional[_T]
        else:
            return str_as_hint(value, real_type)  # e.g. Optional[List[_T]]
    elif issubclass(origin, list):
        elem_type = get_args(hint)[0]
        if isinstance(value, str):
            return [cast_value(elem_type, x) for x in value.split(separator) if x]
        else:
            return [cast_value(elem_type, value)]
    else:
        raise TypeError(f"Unsupported origin: {origin}")


def is_string_namespace(namespace: Namespace) -> bool:
    for value in vars(namespace).values():
        if not isinstance(value, str):
            return False
    return True


def typing_namespace(
    namespace: Namespace,
    cls: Type[AnyNamespace],
    separator=VALUE_SEPARATOR,
) -> AnyNamespace:
    if not is_string_namespace(namespace):
        raise TypeError("All properties in the namespace must be of type string")

    result = cls()
    hints = get_type_hints(cls)
    for member, hint in hints.items():
        if hasattr(namespace, member):
            value = getattr(namespace, member)
            if value is not None:
                setattr(result, member, str_as_hint(value, hint, separator=separator))
            else:
                setattr(result, member, None)
        elif is_optional_hint(hint):
            assert not hasattr(namespace, member)
            setattr(result, member, None)
    return result
