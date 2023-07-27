# -*- coding: utf-8 -*-

from multiprocessing import Process
from time import sleep
from unittest import TestCase, main

from ffstreamer.memory.spsc_queue import SpscQueue, SpscQueueProducer


def on_subprocess(producer: SpscQueueProducer) -> None:
    for i in range(producer.maxsize):
        producer.put(bytes([i, i, i, i]))
        if i % 10 == 0:
            sleep(0.01)


class SpscQueueTestCase(TestCase):
    def test_default(self):
        queue = SpscQueue(100, 4)
        process = Process(target=on_subprocess, args=(queue.producer,))
        process.start()

        for i in range(queue.consumer.maxsize):
            data = queue.consumer.get()
            if i % 20 == 0:
                sleep(0.01)
            self.assertEqual(bytes([i, i, i, i]), data)

        process.join()


if __name__ == "__main__":
    main()
