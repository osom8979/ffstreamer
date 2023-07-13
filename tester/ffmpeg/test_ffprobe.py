# -*- coding: utf-8 -*-

import os
from contextlib import contextmanager
from copy import deepcopy
from unittest import TestCase, main

from static_ffmpeg import add_paths, run

from ffstreamer.ffmpeg.ffprobe import inspect_source
from tester.ffmpeg.assets import get_big_buck_bunny_trailer_path


@contextmanager
def use_static_ffprobe():
    original_path = deepcopy(os.environ["PATH"])
    try:
        add_paths()
        ffmpeg_path, ffprobe_path = run.get_or_fetch_platform_executables_else_raise()
        assert ffmpeg_path is not None
        assert ffprobe_path is not None
        yield ffprobe_path
    finally:
        os.environ["PATH"] = original_path


class FFprobeTestCase(TestCase):
    def test_inspect_source(self):
        video_path = get_big_buck_bunny_trailer_path()
        self.assertTrue(os.path.isfile(video_path))

        with use_static_ffprobe() as ffprobe_path:
            self.assertTrue(os.path.isfile(ffprobe_path))

            inspect_result = inspect_source(video_path, ffprobe_path)
            self.assertIsInstance(inspect_result, dict)

            streams = inspect_result["streams"]
            video_streams = list(filter(lambda x: x["codec_type"] == "video", streams))
            video_stream = video_streams[0]
            width = video_stream["width"]
            height = video_stream["height"]

            self.assertEqual(width, 480)
            self.assertEqual(height, 270)


if __name__ == "__main__":
    main()
