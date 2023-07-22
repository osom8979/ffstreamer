# -*- coding: utf-8 -*-

from collections import deque
from ctypes import c_uint8
from dataclasses import dataclass
from multiprocessing import Pipe
from multiprocessing import connection as conn
from multiprocessing.sharedctypes import RawArray
from queue import Empty, Full
from typing import Deque, List, Optional


@dataclass
class SpscRawArrays:
    buffer_size: int
    buffers: List[RawArray]

    @property
    def size(self) -> int:
        return len(self.buffers)


class SpscQueueProducer:
    _deque: Deque[int]

    def __init__(
        self,
        buffer: SpscRawArrays,
        working_sender: conn.Connection,
        pending_receiver: conn.Connection,
    ):
        self._buffer = buffer
        self._working_sender = working_sender
        self._pending_receiver = pending_receiver
        self._deque = deque(maxlen=buffer.size)
        for i in range(buffer.size):
            self._deque.append(i)

    @property
    def queue_size(self) -> int:
        return self._buffer.size

    @property
    def buffer_size(self) -> int:
        return self._buffer.buffer_size

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
        self._buffer.buffers[index][begin:end] = data
        self._working_sender.send(index)


class SpscQueueConsumer:
    def __init__(
        self,
        buffer: SpscRawArrays,
        working_receiver: conn.Connection,
        pending_sender: conn.Connection,
    ):
        self._buffer = buffer
        self._working_receiver = working_receiver
        self._pending_sender = pending_sender
        self._deque = deque(maxlen=buffer.size)

    @property
    def queue_size(self) -> int:
        return self._buffer.size

    @property
    def buffer_size(self) -> int:
        return self._buffer.buffer_size

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

        result = bytes(self._buffer.buffers[index][:])
        self._pending_sender.send(index)
        return result


class SpscQueue:
    """
    Single Producer Single Consumer Queue
    """

    _queue_size: int
    _buffer_size: int
    _buffers: List[RawArray]

    def __init__(self, queue_size=8, buffer_size=4*1024*1024):
        self._queue_size = queue_size
        self._buffer_size = buffer_size
        self._buffers = [RawArray(c_uint8, buffer_size) for _ in range(queue_size)]

        working = Pipe()
        self._working_receiver = working[0]
        self._working_sender = working[1]

        pending = Pipe()
        self._pending_receiver = pending[0]
        self._pending_sender = pending[1]

        buffer = SpscRawArrays(
            buffer_size=self._buffer_size,
            buffers=self._buffers,
        )
        self._producer = SpscQueueProducer(
            buffer,
            self._working_sender,
            self._pending_receiver,
        )
        self._consumer = SpscQueueConsumer(
            buffer,
            self._working_receiver,
            self._pending_sender,
        )

    @property
    def producer(self):
        return self._producer

    @property
    def consumer(self):
        return self._consumer
