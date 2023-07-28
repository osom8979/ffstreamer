# -*- coding: utf-8 -*-

import os.path
from multiprocessing import Event
from os import path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from numpy import uint8, zeros

from ffstreamer.ffmpeg.ffprobe import inspect_source_size
from ffstreamer.memory.spsc_queue import SpscQueue
from ffstreamer.pyav.pyav_sender import create_pyav_sender_process


class PyavSenderTestCase(TestCase):
    def test_default(self):
        with TemporaryDirectory(suffix="ffstreamer.pyav.pyav_sender") as tempdir:
            self.assertTrue(os.path.isdir(tempdir))

            file_format = "mp4"
            file_name = f"video.{file_format}"
            video_path = path.join(tempdir, file_name)
            self.assertFalse(os.path.isfile(video_path))

            shape = 100, 50, 3
            item_size = shape[0] * shape[1] * shape[2]
            queue = SpscQueue(10, item_size)
            video_frames = 1000
            black_image = zeros(shape, dtype=uint8)
            done = Event()
            process = create_pyav_sender_process(
                video_path,
                file_format,
                shape,
                queue.consumer,
                done,
            )
            process.start()

            black_image_size = len(black_image.tobytes())
            self.assertEqual(black_image_size, item_size)

            for _ in range(video_frames):
                queue.producer.put(black_image.tobytes())

            done.set()
            process.join()
            self.assertTrue(os.path.isfile(video_path))

            video_width, video_height = inspect_source_size(video_path)
            self.assertEqual(shape[0], video_height)
            self.assertEqual(shape[1], video_width)

        self.assertFalse(os.path.isfile(video_path))


if __name__ == "__main__":
    main()
