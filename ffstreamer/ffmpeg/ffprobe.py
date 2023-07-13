# -*- coding: utf-8 -*-

from json import loads as json_loads
from subprocess import check_output
from typing import Any


def inspect_source(src: str, ffprobe_path="ffprobe") -> Any:
    ffprobe_command = [
        ffprobe_path,
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        src,
    ]
    output = check_output(ffprobe_command).decode("utf-8")
    return json_loads(output)
