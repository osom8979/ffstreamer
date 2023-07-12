# -*- coding: utf-8 -*-

from argparse import Namespace
from typing import Optional, TypeVar

AnyNamespace = TypeVar("AnyNamespace", bound=Namespace)


def left_join(*namespaces: Optional[AnyNamespace]) -> AnyNamespace:
    """
    Insert if the attribute in the **left** namespace does not exist or is None.
    """

    if len(namespaces) == 0:
        raise IndexError("At least one argument is required")

    left = namespaces[0]
    for ns in namespaces[1:]:
        if not ns:
            continue

        if left is None:
            assert isinstance(ns, Namespace)
            left = ns
            continue

        for key, value in vars(ns).items():
            if getattr(left, key, None) is None:
                setattr(left, key, value)

    if left is None:
        raise ValueError("At least one argument must not be None")

    return left


def right_join(*namespaces: Optional[AnyNamespace]) -> AnyNamespace:
    """
    Insert if the attribute in the **right** namespace does not exist or is None.
    """

    if len(namespaces) == 0:
        raise IndexError("At least one argument is required")

    nss = list(namespaces)
    nss.reverse()
    return left_join(*nss)


def strip_none_attributes(namespace: AnyNamespace) -> AnyNamespace:
    keys = list(vars(namespace).keys())
    for key in keys:
        if getattr(namespace, key) is None:
            delattr(namespace, key)
    return namespace
