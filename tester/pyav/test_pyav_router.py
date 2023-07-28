# -*- coding: utf-8 -*-

from multiprocessing import Event
from unittest import TestCase, main

from numpy import concatenate, uint8
from numpy.random import randint

from ffstreamer.memory.spsc_queue import SpscQueue
from ffstreamer.np.image import make_image_with_shape
from ffstreamer.pyav.pyav_router import create_pyav_router_process


class PyavRouterTestCase(TestCase):
    def test_synchronize(self):
        width, height = 100, 50
        shape = height, width, 3
        item_size = height * width * shape[-1]
        overlay_shape = height, width, 4
        overlay_item_size = height * width * overlay_shape[-1]
        mask_shape = height, width, 1
        queue_size = 10

        receiver = SpscQueue(queue_size, item_size)
        improc = SpscQueue(1, item_size)
        overlay = SpscQueue(1, overlay_item_size)
        sender = SpscQueue(queue_size, item_size)

        done = Event()
        process = create_pyav_router_process(
            shape,
            receiver.consumer,
            improc.producer,
            overlay.consumer,
            sender.producer,
            done,
            synchronize=True,
        )
        process.start()

        test_image = randint(0, 256, shape, dtype=uint8)
        test_image_data = test_image.tobytes()
        test_image_size = len(test_image_data)
        self.assertEqual(test_image_size, item_size)

        receiver.producer.put(test_image_data)
        improc_data = improc.consumer.get()
        self.assertEqual(improc_data, test_image_data)

        improc_image = make_image_with_shape(shape, improc_data)
        mask = randint(0, 256, mask_shape, dtype=uint8)
        bgra = concatenate((improc_image, mask), axis=-1)
        self.assertTupleEqual(bgra.shape, overlay_shape)

        overlay.producer.put(bgra.tobytes())
        send_data = sender.consumer.get()
        self.assertEqual(len(send_data), test_image_size)

        send_image = make_image_with_shape(shape, send_data)
        self.assertTupleEqual(send_image.shape, shape)

        done.set()
        process.join()


if __name__ == "__main__":
    main()
