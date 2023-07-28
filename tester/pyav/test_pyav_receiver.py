# -*- coding: utf-8 -*-

import os.path
from multiprocessing import Event
from unittest import TestCase, main

from numpy import ndarray, uint8
from numpy.typing import NDArray

from ffstreamer.ffmpeg.ffprobe import inspect_source_size
from ffstreamer.memory.spsc_queue import SpscQueue
from ffstreamer.pyav.pyav_receiver import create_pyav_receiver_process
from tester.assets import get_big_buck_bunny_trailer_path


class PyavReceiverTestCase(TestCase):
    def test_default(self):
        video_path = get_big_buck_bunny_trailer_path()
        video_width, video_height = inspect_source_size(video_path)
        self.assertTrue(os.path.isfile(video_path))

        shape = video_height, video_width, 3
        item_size = shape[0] * shape[1] * shape[2]
        queue = SpscQueue(10, item_size)
        done = Event()
        process = create_pyav_receiver_process(
            video_path,
            queue.producer,
            done,
        )
        process.start()

        for i in range(queue.consumer.maxsize):
            data = queue.consumer.get()
            image: NDArray[uint8] = ndarray(shape, uint8, data)
            self.assertEqual(image.shape[0], video_height)
            self.assertEqual(image.shape[1], video_width)
            self.assertEqual(image.shape[2], 3)

        done.set()
        process.join()


if __name__ == "__main__":
    main()
