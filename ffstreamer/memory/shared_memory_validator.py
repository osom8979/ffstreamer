# -*- coding: utf-8 -*-

from contextlib import contextmanager
from multiprocessing.shared_memory import SharedMemory
from typing import Any, Generator, NamedTuple, Optional
from uuid import uuid4

from ffstreamer.memory.shared_memory_utils import (
    attach_shared_memory,
    create_shared_memory,
    destroy_shared_memory,
)


class SharedMemoryTestInfo(NamedTuple):
    name: str
    data: str


@contextmanager
def register_shared_memory(disable=False) -> Generator[SharedMemoryTestInfo, Any, None]:
    sm: Optional[SharedMemory]

    if disable:
        test_sm_data = str()
        test_sm_pass_bytes = bytes()
        sm = None
        test_sm_name = str()
    else:
        test_sm_data = uuid4().hex
        test_sm_pass_bytes = bytes.fromhex(test_sm_data)
        sm = create_shared_memory(len(test_sm_pass_bytes))
        test_sm_name = sm.name

    try:
        if sm:
            sm.buf[:] = test_sm_pass_bytes
        yield SharedMemoryTestInfo(test_sm_name, test_sm_data)
    finally:
        if sm:
            destroy_shared_memory(sm)


def validate_shared_memory(name: str, data: str) -> bool:
    if name and data:
        try:
            with attach_shared_memory(name) as sm:
                return bytes(sm.buf[:]) == bytes.fromhex(data)
        except:  # noqa
            pass
    return False
