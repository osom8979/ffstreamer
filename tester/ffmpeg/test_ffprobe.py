# -*- coding: utf-8 -*-

import os
from unittest import TestCase, main

from ffstreamer.ffmpeg.ffprobe import inspect_source
from ffstreamer.ffmpeg.static_lib import StaticFFmpegPaths
from tester.assets import get_big_buck_bunny_trailer_path


class FFprobeTestCase(TestCase):
    def test_inspect_source(self):
        video_path = get_big_buck_bunny_trailer_path()
        self.assertTrue(os.path.isfile(video_path))

        with StaticFFmpegPaths() as paths:
            self.assertTrue(os.path.isfile(paths.ffprobe_path))

            inspect_result = inspect_source(video_path, paths.ffprobe_path)
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
