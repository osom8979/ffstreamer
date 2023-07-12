# -*- coding: utf-8 -*-

from typing import Dict, Final, Optional

from ffstreamer.system.environ import environ_dict

ENVIRONMENT_PREFIX: Final[str] = "FFSTREAMER_"
ENVIRONMENT_SUFFIX: Final[str] = ""
ENVIRONMENT_FILE_PREFIX: Final[str] = "FFSTREAMER_"
ENVIRONMENT_FILE_SUFFIX: Final[str] = "_FILE"


def get_env_key(
    key: str,
    prefix=ENVIRONMENT_PREFIX,
    suffix=ENVIRONMENT_SUFFIX,
) -> str:
    return prefix + key.upper() + suffix


def get_env(
    key: str,
    prefix=ENVIRONMENT_PREFIX,
    suffix=ENVIRONMENT_SUFFIX,
    *,
    envs: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    environ = envs if envs else environ_dict()
    return environ.get(get_env_key(key, prefix, suffix), None)


def get_file_env(
    key: str,
    prefix=ENVIRONMENT_FILE_PREFIX,
    suffix=ENVIRONMENT_FILE_SUFFIX,
    *,
    envs: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    environ = envs if envs else environ_dict()
    path = environ.get(get_env_key(key, prefix, suffix), None)
    if path is None:
        return None
    with open(path) as f:
        return f.read()


def get_envs(
    prefix=ENVIRONMENT_PREFIX,
    suffix=ENVIRONMENT_SUFFIX,
    *,
    envs: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    result = dict()
    key_begin = len(prefix)
    key_end = (-1) * len(suffix) if len(suffix) >= 1 else None
    environ = envs if envs else environ_dict()
    for key, value in environ.items():
        if key.startswith(prefix) and key.endswith(suffix):
            raw_key = key[key_begin:key_end]
            if raw_key.isupper():
                result[raw_key.lower()] = value
    return result


def get_file_envs(
    prefix=ENVIRONMENT_FILE_PREFIX,
    suffix=ENVIRONMENT_FILE_SUFFIX,
    *,
    envs: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    result = dict()
    key_begin = len(prefix)
    key_end = (-1) * len(suffix) if len(suffix) >= 1 else None
    environ = envs if envs else environ_dict()
    for key, value in environ.items():
        if key.startswith(prefix) and key.endswith(suffix):
            raw_key = key[key_begin:key_end]
            if raw_key.isupper():
                with open(value) as f:
                    result[raw_key.lower()] = f.read()
    return result
