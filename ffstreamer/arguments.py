# -*- coding: utf-8 -*-

from argparse import REMAINDER, ArgumentParser, Namespace, RawDescriptionHelpFormatter
from functools import lru_cache
from typing import Final, List, Optional

from ffstreamer.logging.logging import SEVERITIES, SEVERITY_NAME_INFO
from ffstreamer.module.module import MODULE_NAME_PREFIX

PROG: Final[str] = "ffstreamer"
DESCRIPTION: Final[str] = "FFmpeg Streamer"
EPILOG: Final[str] = ""

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
        "-i",
        action="append",
        nargs="*",
        default=list(),
        help="List of FFmpeg input command lines",
    )
    parser.add_argument(
        "-o",
        action="append",
        nargs="*",
        default=list(),
        help="List of FFmpeg output command lines",
    )

    # -----------
    # I/O options
    # -----------

    parser.add_argument(
        "--map",
        "-m",
        action="append",
        default=list(),
        help="Stream Mapping (format is 'i:[vasdt]:o')",
    )

    parser.add_argument(
        "module",
        default=None,
        nargs="?",
        help="Module name",
    )
    parser.add_argument(
        "opts",
        nargs=REMAINDER,
        help="Arguments of module",
    )

    return parser


def get_default_arguments(
    cmdline: Optional[List[str]] = None,
    namespace: Optional[Namespace] = None,
) -> Namespace:
    parser = default_argument_parser()
    return parser.parse_known_args(cmdline, namespace)[0]
