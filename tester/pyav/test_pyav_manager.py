# -*- coding: utf-8 -*-

import os.path
from os import path
from tempfile import TemporaryDirectory
from unittest import IsolatedAsyncioTestCase, main, skip

from ffstreamer.ffmpeg.ffprobe import inspect_source_size
from ffstreamer.pyav.pyav_manager import PyavManager
from tester.assets import get_big_buck_bunny_trailer_path


class PyavSenderTestCase(IsolatedAsyncioTestCase):
    @skip(reason="Too slow")
    async def test_default(self):
        source = get_big_buck_bunny_trailer_path()
        width, height = inspect_source_size(source)
        self.assertTrue(os.path.isfile(source))

        with TemporaryDirectory(suffix="pyav_manager", prefix="tester") as tempdir:
            # tempdir = "."
            self.assertTrue(os.path.isdir(tempdir))

            file_format = "mp4"
            file_name = f"video.{file_format}"
            destination = path.join(tempdir, file_name)
            self.assertFalse(os.path.isfile(destination))

            manager = PyavManager(
                source,
                destination,
                file_format,
                width,
                height,
                synchronize=True,
            )
            await manager.run_until_complete()
            self.assertTrue(os.path.isfile(destination))

            dest_width, dest_height = inspect_source_size(destination)
            self.assertEqual(width, dest_width)
            self.assertEqual(height, dest_height)


if __name__ == "__main__":
    main()
