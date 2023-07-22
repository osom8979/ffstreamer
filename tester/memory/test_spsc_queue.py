# -*- coding: utf-8 -*-

from unittest import TestCase, main
from multiprocessing import Process

from ffstreamer.memory.spsc_queue import SpscQueue, SpscQueueProducer


def on_subprocess(producer: SpscQueueProducer) -> None:
    for i in range(producer.queue_size):
        producer.pull_nowait()
        producer.put(bytes([i, i, i, i]))


class SpscQueueTestCase(TestCase):
    def test_default(self):
        queue = SpscQueue(100, 4)
        process = Process(target=on_subprocess, args=(queue.producer,))
        process.start()

        for i in range(queue.consumer.queue_size):
            queue.consumer.pull_nowait()
            data = queue.consumer.get()
            self.assertEqual(bytes([i, i, i, i]), data)

        process.join()


if __name__ == "__main__":
    main()
