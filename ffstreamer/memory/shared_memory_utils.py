# -*- coding: utf-8 -*-

import os
from multiprocessing.shared_memory import SharedMemory


def _unregister_shared_memory_tracker(sm: SharedMemory) -> None:
    # https://bugs.python.org/issue39959
    if os.name != "nt":
        from multiprocessing.resource_tracker import unregister  # noqa

        unregister(getattr(sm, "_name"), "shared_memory")


class _AttachSharedMemoryContext:
    def __init__(self, name: str):
        self.name = name

    def __enter__(self) -> SharedMemory:
        self.sm = SharedMemory(name=self.name)
        return self.sm

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sm.close()
        _unregister_shared_memory_tracker(self.sm)


def attach_shared_memory(name: str):
    return _AttachSharedMemoryContext(name)


def create_shared_memory(buffer_size: int) -> SharedMemory:
    return SharedMemory(create=True, size=buffer_size)


def destroy_shared_memory(sm: SharedMemory) -> None:
    sm.close()
    sm.unlink()
