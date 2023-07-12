# -*- coding: utf-8 -*-

from collections import deque
from multiprocessing.shared_memory import SharedMemory
from typing import Deque, Dict, NamedTuple, Optional, Union

from ffstreamer.memory.shared_memory_utils import (
    create_shared_memory,
    destroy_shared_memory,
)

SHARED_MEMORY_INFINITY_QUEUE = 0


class Written(NamedTuple):
    sm_name: str
    offset: int
    end: int

    @property
    def size(self) -> int:
        return self.end - self.offset


class SharedMemoryQueue:
    _max_queue: int
    _waiting: Deque[SharedMemory]
    _working: Dict[str, SharedMemory]

    def __init__(self, max_queue=SHARED_MEMORY_INFINITY_QUEUE):
        self._max_queue = max_queue
        self._waiting = deque()
        self._working = dict()

    @property
    def max_queue(self) -> int:
        return self._max_queue

    def clear_waiting(self) -> None:
        while self._waiting:
            sm = self._waiting.popleft()
            destroy_shared_memory(sm)
        assert not self._waiting

    def clear_working(self) -> None:
        while self._working:
            _, sm = self._working.popitem()
            destroy_shared_memory(sm)
        assert not self._working

    def clear(self) -> None:
        self.clear_waiting()
        self.clear_working()

    def size_waiting(self) -> int:
        return len(self._waiting)

    def size_working(self) -> int:
        return len(self._working)

    def find_working(self, key: str) -> SharedMemory:
        return self._working[key]

    def secure_worker(self, size: int) -> SharedMemory:
        try:
            sm = self._waiting.popleft()
            if sm.size < size:
                destroy_shared_memory(sm)
                raise BufferError
        except (IndexError, BufferError):
            sm = create_shared_memory(size)
        assert sm is not None
        self._working[sm.name] = sm
        return sm

    def write(self, data: Union[bytes, memoryview], offset=0) -> Written:
        if isinstance(data, memoryview):
            return self.write(data.tobytes(), offset)

        assert isinstance(data, bytes)
        end = offset + len(data)
        sm = self.secure_worker(end)
        sm.buf[offset:end] = data
        return Written(sm.name, offset, end)

    def restore(self, name: str) -> None:
        self._waiting.append(self._working.pop(name))

    @staticmethod
    def read(name: str, offset=0, size: Optional[int] = None) -> bytes:
        sm = SharedMemory(name=name)
        if size is None:
            return bytes(sm.buf[offset:])
        else:
            if size <= 0:
                raise ValueError("The 'size' argument must be greater than 0")
            end = offset + size
            return bytes(sm.buf[offset:end])

    class RentalManager:
        __slots__ = ("_sm", "_smq")

        def __init__(self, sm: SharedMemory, smq: "SharedMemoryQueue"):
            self._sm = sm
            self._smq = smq

        def __enter__(self) -> SharedMemory:
            return self._sm

        def __exit__(self, exc_type, exc_value, tb):
            self._smq.restore(self._sm.name)

    def rent(self, buffer_byte: int) -> RentalManager:
        return self.RentalManager(self.secure_worker(buffer_byte), self)

    class MultiRentalManager:
        __slots__ = ("_sms", "_smq")

        def __init__(self, sms: Dict[str, SharedMemory], smq: "SharedMemoryQueue"):
            self._sms = sms
            self._smq = smq

        def __enter__(self) -> Dict[str, SharedMemory]:
            return self._sms

        def __exit__(self, exc_type, exc_value, tb):
            for sm in self._sms.values():
                self._smq.restore(sm.name)

    def multi_rent(self, rental_size: int, buffer_byte: int) -> MultiRentalManager:
        if rental_size <= 0 or buffer_byte <= 0:
            return self.MultiRentalManager(dict(), self)

        sms = [self.secure_worker(buffer_byte) for _ in range(rental_size)]
        return self.MultiRentalManager(
            sms={sm.name: sm for sm in sms},
            smq=self,
        )
