# -*- coding: utf-8 -*-

from os import environ
from typing import Dict, Optional


def environ_dict() -> Dict[str, str]:
    return {k: str(environ.get(k)) for k in environ if environ}


def exchange_env(key: str, exchange: Optional[str]) -> Optional[str]:
    result = environ.get(key)
    if result is not None:
        environ.pop(key)
    if exchange is not None:
        environ[key] = exchange
    return result
