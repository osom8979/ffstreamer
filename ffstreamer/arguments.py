# -*- coding: utf-8 -*-

from argparse import REMAINDER, ArgumentParser, Namespace, RawDescriptionHelpFormatter
from functools import lru_cache
from typing import Final, List, Optional

from ffstreamer.ffmpeg.ffmpeg import (
    DEFAULT_FFMPEG_INPUT_FORMAT,
    DEFAULT_FFMPEG_OUTPUT_FORMAT,
)
from ffstreamer.logging.logging import SEVERITIES, SEVERITY_NAME_INFO
from ffstreamer.module.variables import MODULE_NAME_PREFIX, MODULE_PIPE_SEPARATOR

PROG: Final[str] = "ffstreamer"
DESCRIPTION: Final[str] = "FFmpeg Streamer"
EPILOG = f"""
Examples:

  Debugging options:
    $ {PROG} -c -d -vv ...

  RTSP to RTSP:
    $ {PROG} "rtsp://ip-camera/stream" rtsp "rtsp://localhost:8554/stream"
"""


DEFAULT_SEVERITY: Final[str] = SEVERITY_NAME_INFO
DEFAULT_MODULE_PREFIX: Final[str] = MODULE_NAME_PREFIX


@lru_cache
def version() -> str:
    # [IMPORTANT] Avoid 'circular import' issues
    from ffstreamer import __version__

    return __version__


def default_argument_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog=PROG,
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--colored-logging",
        "-c",
        action="store_true",
        default=False,
        help="Use colored logging",
    )
    parser.add_argument(
        "--simple-logging",
        "-s",
        action="store_true",
        default=False,
        help="Use simple logging",
    )
    parser.add_argument(
        "--severity",
        choices=SEVERITIES,
        default=DEFAULT_SEVERITY,
        help=f"Logging severity (default: '{DEFAULT_SEVERITY}')",
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        default=False,
        help="Enable debugging mode and change logging severity to 'DEBUG'",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Be more verbose/talkative during the operation",
    )
    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=version(),
    )

    # --------------
    # Module options
    # --------------

    parser.add_argument(
        "--module-prefix",
        metavar="prefix",
        default=DEFAULT_MODULE_PREFIX,
        help=f"The prefix of the module (default: '{DEFAULT_MODULE_PREFIX}')",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        default=False,
        help="Prints a list of available modules",
    )

    # --------------
    # FFmpeg options
    # --------------

    parser.add_argument(
        "--ffmpeg-path",
        default="ffmpeg",
        help="FFmpeg command path",
    )
    parser.add_argument(
        "--ffprobe-path",
        default="ffprobe",
        help="FFprobe command path",
    )
    parser.add_argument(
        "--input",
        "-i",
        default=DEFAULT_FFMPEG_INPUT_FORMAT,
        help=(
            "Commandline arguments of the FFmpeg input pipeline"
            f" (Default is '{DEFAULT_FFMPEG_INPUT_FORMAT}')"
        ),
    )
    parser.add_argument(
        "--input-channels",
        type=int,
        default=3,
        help="Number of channels to pipeline",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=DEFAULT_FFMPEG_OUTPUT_FORMAT,
        help=(
            "Commandline arguments of the FFmpeg output pipeline"
            f" (Default is '{DEFAULT_FFMPEG_OUTPUT_FORMAT}')"
        ),
    )
    parser.add_argument(
        "--preview",
        "-p",
        action="store_true",
        default=False,
        help="Display the preview window",
    )

    parser.add_argument(
        "source",
        help="Input source URL",
    )
    parser.add_argument(
        "format",
        help="Output file format",
    )
    parser.add_argument(
        "destination",
        help="Output URL",
    )

    parser.add_argument(
        "opts",
        nargs=REMAINDER,
        help=f"Module pipelines (Module pipe separator is '{MODULE_PIPE_SEPARATOR}')",
    )

    return parser


def get_default_arguments(
    cmdline: Optional[List[str]] = None,
    namespace: Optional[Namespace] = None,
) -> Namespace:
    parser = default_argument_parser()
    return parser.parse_known_args(cmdline, namespace)[0]
