# -*- coding: utf-8 -*-

from collections import deque
from ctypes import c_uint8
from multiprocessing import Pipe
from multiprocessing import connection as conn
from multiprocessing.sharedctypes import RawArray
from queue import Empty, Full
from typing import Any, Deque, List, Optional

RawArrayType = Any


class SpscStore:
    _arrays: List[RawArrayType]

    def __init__(self, array_size: int, item_size: int):
        assert array_size >= 1
        assert item_size >= 1
        self._arrays = [RawArray(c_uint8, item_size) for _ in range(array_size)]
        self._item_size = item_size

    def __getitem__(self, index: int) -> RawArrayType:
        return self._arrays.__getitem__(index)

    @property
    def maxsize(self) -> int:
        return len(self._arrays)

    @property
    def item_size(self) -> int:
        return self._item_size


class SpscQueueProducer:
    _buffer: Deque[int]

    def __init__(
        self,
        store: SpscStore,
        working_sender: conn.Connection,
        pending_receiver: conn.Connection,
    ):
        self._store = store
        self._working_sender = working_sender
        self._pending_receiver = pending_receiver
        self._buffer = deque(maxlen=self._store.maxsize)

        for i in range(store.maxsize):
            self._buffer.append(i)

    @property
    def maxsize(self) -> int:
        return self._store.maxsize

    @property
    def item_size(self) -> int:
        return self._store.item_size

    @property
    def full(self) -> bool:
        return not self._buffer

    def close(self) -> None:
        self._working_sender.close()
        self._pending_receiver.close()

    def pull_nowait(self) -> None:
        while self._pending_receiver.poll():
            self._buffer.append(self._pending_receiver.recv())

    def put_and_working(self, index: int, data: bytes, begin=0) -> None:
        end = begin + len(data)
        self._store[index][begin:end] = data
        self._working_sender.send(index)

    def put_nowait(self, data: bytes, begin=0) -> None:
        if not self._buffer:
            raise Full()
        self.put_and_working(self._buffer.popleft(), data, begin)

    def put_with_receiver(
        self, data: bytes, begin=0, timeout: Optional[float] = None
    ) -> None:
        if timeout is None:
            index = self._pending_receiver.recv()
        else:
            if timeout <= 0:
                raise Full()
            if self._pending_receiver.poll(timeout):
                index = self._pending_receiver.recv()
            else:
                raise Full()
        self.put_and_working(index, data, begin)

    def put(self, data: bytes, begin=0, timeout: Optional[float] = None) -> None:
        self.pull_nowait()
        if self._buffer:
            return self.put_nowait(data, begin)
        else:
            return self.put_with_receiver(data, begin, timeout)


class SpscQueueConsumer:
    _buffer: Deque[int]

    def __init__(
        self,
        store: SpscStore,
        working_receiver: conn.Connection,
        pending_sender: conn.Connection,
    ):
        self._store = store
        self._working_receiver = working_receiver
        self._pending_sender = pending_sender
        self._buffer = deque(maxlen=self._store.maxsize)

    @property
    def maxsize(self) -> int:
        return self._store.maxsize

    @property
    def item_size(self) -> int:
        return self._store.item_size

    @property
    def empty(self) -> bool:
        return not self._buffer

    def close(self) -> None:
        self._working_receiver.close()
        self._pending_sender.close()

    def pull_nowait(self) -> None:
        while self._working_receiver.poll():
            self._buffer.append(self._working_receiver.recv())

    def get_and_pending(self, index: int) -> bytes:
        result = bytes(self._store[index][:])
        self._pending_sender.send(index)
        return result

    def get_nowait(self) -> bytes:
        if not self._buffer:
            raise Empty()
        return self.get_and_pending(self._buffer.popleft())

    def get_with_receiver(self, timeout: Optional[float] = None) -> bytes:
        if timeout is None:
            index = self._working_receiver.recv()
        else:
            if timeout <= 0:
                raise Empty()
            if self._working_receiver.poll(timeout):
                index = self._working_receiver.recv()
            else:
                raise Empty()
        return self.get_and_pending(index)

    def get(self, timeout: Optional[float] = None) -> bytes:
        self.pull_nowait()
        if self._buffer:
            return self.get_nowait()
        else:
            return self.get_with_receiver(timeout)

    def get_latest_nowait(self) -> bytes:
        if not self._buffer:
            raise Empty()

        while True:
            index = self._buffer.popleft()
            if self._buffer:
                self._pending_sender.send(index)
            else:
                return self.get_and_pending(index)


class SpscQueue:
    """
    Single Producer Single Consumer Queue
    """

    _store: SpscStore

    def __init__(self, queue_size=8, item_size=4 * 1024 * 1024):
        self._store = SpscStore(queue_size, item_size)
        working_receiver, working_sender = Pipe()
        pending_receiver, pending_sender = Pipe()
        self._producer = SpscQueueProducer(
            self._store,
            working_sender,
            pending_receiver,
        )
        self._consumer = SpscQueueConsumer(
            self._store,
            working_receiver,
            pending_sender,
        )

    @property
    def producer(self):
        return self._producer

    @property
    def consumer(self):
        return self._consumer
