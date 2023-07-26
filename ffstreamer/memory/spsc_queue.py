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

    def __len__(self) -> int:
        return self._arrays.__len__()

    def __getitem__(self, index: int) -> RawArrayType:
        return self._arrays.__getitem__(index)

    @property
    def item_size(self) -> int:
        return self._item_size


class SpscQueueProducer:
    _deque: Deque[int]

    def __init__(
        self,
        store: SpscStore,
        working_sender: conn.Connection,
        pending_receiver: conn.Connection,
    ):
        self._store = store
        self._working_sender = working_sender
        self._pending_receiver = pending_receiver
        self._deque = deque(maxlen=len(store))

        for i in range(len(store)):
            self._deque.append(i)

    @property
    def queue_size(self) -> int:
        return len(self._store)

    @property
    def item_size(self) -> int:
        return self._store.item_size

    def pull_nowait(self) -> None:
        while self._pending_receiver.poll():
            self._deque.append(self._pending_receiver.recv())

    def put(self, data: bytes, begin=0, timeout: Optional[float] = None) -> None:
        index: int
        if self._deque:
            index = self._deque.popleft()
        else:
            if timeout is None:
                index = self._pending_receiver.recv()
            else:
                if timeout <= 0:
                    raise Full()
                if self._pending_receiver.poll(timeout):
                    index = self._pending_receiver.recv()
                else:
                    raise Full()

        end = begin + len(data)
        self._store[index][begin:end] = data
        self._working_sender.send(index)


class SpscQueueConsumer:
    _deque: Deque[int]

    def __init__(
        self,
        store: SpscStore,
        working_receiver: conn.Connection,
        pending_sender: conn.Connection,
    ):
        self._store = store
        self._working_receiver = working_receiver
        self._pending_sender = pending_sender
        self._deque = deque(maxlen=len(store))

    @property
    def queue_size(self) -> int:
        return len(self._store)

    @property
    def item_size(self) -> int:
        return self._store.item_size

    def pull_nowait(self) -> None:
        while self._working_receiver.poll():
            self._deque.append(self._working_receiver.recv())

    def get(self, timeout: Optional[float] = None) -> bytes:
        index: int
        if self._deque:
            index = self._deque.popleft()
        else:
            if timeout is None:
                index = self._working_receiver.recv()
            else:
                if timeout <= 0:
                    raise Empty()
                if self._working_receiver.poll(timeout):
                    index = self._working_receiver.recv()
                else:
                    raise Empty()

        result = bytes(self._store[index][:])
        self._pending_sender.send(index)
        return result


class SpscQueue:
    """
    Single Producer Single Consumer Queue
    """

    _store: SpscStore

    def __init__(self, queue_size=8, item_size=4 * 1024 * 1024):
        self._store = SpscStore(queue_size, item_size)

        working = Pipe()
        self._working_receiver = working[0]
        self._working_sender = working[1]

        pending = Pipe()
        self._pending_receiver = pending[0]
        self._pending_sender = pending[1]

        self._producer = SpscQueueProducer(
            self._store,
            self._working_sender,
            self._pending_receiver,
        )
        self._consumer = SpscQueueConsumer(
            self._store,
            self._working_receiver,
            self._pending_sender,
        )

    @property
    def producer(self):
        return self._producer

    @property
    def consumer(self):
        return self._consumer
