# -*- coding: utf-8 -*-

from argparse import REMAINDER, ArgumentParser, Namespace, RawDescriptionHelpFormatter
from functools import lru_cache
from typing import Final, List, Optional

from ffstreamer.ffmpeg.ffmpeg import (
    DEFAULT_FFMPEG_RECV_FORMAT,
    DEFAULT_FFMPEG_SEND_FORMAT,
    DEFAULT_FILE_FORMAT,
    DEFAULT_PIXEL_FORMAT,
)
from ffstreamer.logging.logging import SEVERITIES, SEVERITY_NAME_INFO
from ffstreamer.module.variables import MODULE_NAME_PREFIX, MODULE_PIPE_SEPARATOR

__MODULE_PREFIX_FLAG: Final[str] = "--module-prefix"

PROG: Final[str] = "ffstreamer"
DESCRIPTION: Final[str] = "Support for streaming in asyncio using FFmpeg's pipe IPC"
EPILOG = f"""
Examples:

  Full debugging options:
    $ {PROG} -c -d -vv ...

  Find the module name with a prefix:
    $ {PROG} {__MODULE_PREFIX_FLAG}=prefix_ ...

  Find submodules of a specific module - It must end with dot('.') -:
    $ {PROG} {__MODULE_PREFIX_FLAG}=module.path. ...

  Finds a module specifying both a submodule and a prefix:
    $ {PROG} {__MODULE_PREFIX_FLAG}=module.path.prefix_ ...
"""

CMD_PIXELS: Final[str] = "pixels"
CMD_PIXELS_HELP: Final[str] = "Prints a list of available pixel formats"

CMD_FILES: Final[str] = "files"
CMD_FILES_HELP: Final[str] = "Prints a list of available file formats"

CMD_MODULES: Final[str] = "modules"
CMD_MODULES_HELP: Final[str] = "Prints a list of available modules"
CMD_MODULES_EPILOG = f"""
Examples:

  List of modules 'name'
    $ {PROG} {CMD_MODULES}

  List of modules 'name,version':
    $ {PROG} -v {CMD_MODULES}

  List of modules 'name,version,doc':
    $ {PROG} -vv {CMD_MODULES}

  List of modules 'name,version,doc,apis':
    $ {PROG} -vvv {CMD_MODULES}
"""

CMD_LIST: Final[str] = "list"
CMD_LIST_HELP: Final[str] = f"Equals '{CMD_MODULES}' command"
CMD_LIST_EPILOG: Final[str] = CMD_MODULES_EPILOG

CMD_INSPECT: Final[str] = "inspect"
CMD_INSPECT_HELP: Final[str] = "Inspect the source file"
CMD_INSPECT_EPILOG = f"""
Examples:

  Inspect RTSP source
    $ {PROG} {CMD_INSPECT} rtsp://0.0.0.0:8554/live.sdp
"""

CMD_PIPE: Final[str] = "pipe"
CMD_PIPE_HELP: Final[str] = "Run the pipeline"
CMD_PIPE_EPILOG = f"""
Examples:

  Bypass from RTSP to RTSP.
    $ {PROG} {CMD_PIPE} "rtsp://ip-camera/stream" "rtsp://localhost:8554/stream"

Demonstration:

  Run the RTSP source for testing:
    $ docker run --rm -it \\
        -e ENABLE_TIME_OVERLAY=true \\
        -e RTSP_PORT=9999 \\
        -p 9999:9999 \\
        ullaakut/rtspatt

  Run an RTSP proxy server:
    $ docker run --rm -it \\
        -e MTX_PROTOCOLS=tcp \\
        -p 8554:8554 \\
        -p 1935:1935 \\
        -p 8888:8888 \\
        -p 8889:8889 \\
        bluenviron/mediamtx

  Run {PROG}:
    $ {PROG} -c -d -vv {CMD_PIPE} \\
        --use-uvloop \\
        rtsp://localhost:9999/live.sdp \\
        rtsp://localhost:8554/stream \\
        @bytes2numpy ! @grayscale ! @numpy2bytes

  Play the resulting stream:
    $ ffplay \\
        -fflags nobuffer \\
        -fflags discardcorrupt \\
        -flags low_delay \\
        -framedrop \\
        -avioflags direct \\
        -rtsp_transport tcp \\
        rtsp://localhost:8554/stream
"""

CMD_PYAV: Final[str] = "pyav"
CMD_PYAV_HELP: Final[str] = "Run the pipeline for pyav"

CMD_IO: Final[str] = "io"
CMD_IO_HELP: Final[str] = "Run the pipeline for io"

CMD_RTSP: Final[str] = "rtsp"
CMD_RTSP_HELP: Final[str] = "Run the pipeline for rtsp"

CMDS = (
    CMD_FILES,
    CMD_INSPECT,
    CMD_IO,
    CMD_LIST,
    CMD_MODULES,
    CMD_PIPE,
    CMD_PIXELS,
    CMD_PYAV,
    CMD_RTSP,
)

DEFAULT_SEVERITY: Final[str] = SEVERITY_NAME_INFO
DEFAULT_MODULE_PREFIX: Final[str] = MODULE_NAME_PREFIX


@lru_cache
def version() -> str:
    # [IMPORTANT] Avoid 'circular import' issues
    from ffstreamer import __version__

    return __version__


def add_pixels_parser(subparsers) -> None:
    # noinspection SpellCheckingInspection
    parser = subparsers.add_parser(name=CMD_PIXELS, help=CMD_PIXELS_HELP)
    assert isinstance(parser, ArgumentParser)


def add_files_parser(subparsers) -> None:
    # noinspection SpellCheckingInspection
    parser = subparsers.add_parser(name=CMD_FILES, help=CMD_FILES_HELP)
    assert isinstance(parser, ArgumentParser)


def add_modules_parser(subparsers) -> None:
    # noinspection SpellCheckingInspection
    parser = subparsers.add_parser(
        name=CMD_MODULES,
        help=CMD_MODULES_HELP,
        formatter_class=RawDescriptionHelpFormatter,
        epilog=CMD_MODULES_EPILOG,
    )
    assert isinstance(parser, ArgumentParser)


def add_list_parser(subparsers) -> None:
    # noinspection SpellCheckingInspection
    parser = subparsers.add_parser(
        name=CMD_LIST,
        help=CMD_LIST_HELP,
        formatter_class=RawDescriptionHelpFormatter,
        epilog=CMD_LIST_EPILOG,
    )
    assert isinstance(parser, ArgumentParser)


def add_inspect_parser(subparsers) -> None:
    # noinspection SpellCheckingInspection
    parser = subparsers.add_parser(
        name=CMD_INSPECT,
        help=CMD_INSPECT_HELP,
        formatter_class=RawDescriptionHelpFormatter,
        epilog=CMD_INSPECT_EPILOG,
    )
    assert isinstance(parser, ArgumentParser)
    parser.add_argument("source", help="Source URL")


def add_ffmpeg_commandline_arguments(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--recv-commandline",
        "-i",
        default=DEFAULT_FFMPEG_RECV_FORMAT,
        help="Commandline arguments of the FFmpeg recv pipeline",
    )
    parser.add_argument(
        "--send-commandline",
        "-o",
        default=DEFAULT_FFMPEG_SEND_FORMAT,
        help="Commandline arguments of the FFmpeg send pipeline",
    )


def add_ffmpeg_options_arguments(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--pixel-format",
        default=DEFAULT_PIXEL_FORMAT,
        help=(
            "The pixel format of the frames passed across the pipeline"
            f" (default: '{DEFAULT_PIXEL_FORMAT}')"
        ),
    )
    parser.add_argument(
        "--file-format",
        default=DEFAULT_FILE_FORMAT,
        help=f"Result file format (default: '{DEFAULT_FILE_FORMAT}')",
    )


def add_pipeline_arguments(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--pipe-separator",
        default=MODULE_PIPE_SEPARATOR,
        help=f"The module's pipeline separator (default: '{MODULE_PIPE_SEPARATOR}')",
    )


def add_pipeline_positional_arguments(parser: ArgumentParser) -> None:
    parser.add_argument(
        "source",
        help="Input source URL",
    )
    parser.add_argument(
        "destination",
        help="Output destination URL",
    )
    parser.add_argument(
        "opts",
        nargs=REMAINDER,
        help="Module pipelines arguments",
    )


def add_pipe_parser(subparsers) -> None:
    # noinspection SpellCheckingInspection
    parser = subparsers.add_parser(
        name=CMD_PIPE,
        help=CMD_PIPE_HELP,
        formatter_class=RawDescriptionHelpFormatter,
        epilog=CMD_PIPE_EPILOG,
    )
    assert isinstance(parser, ArgumentParser)
    add_ffmpeg_commandline_arguments(parser)
    add_ffmpeg_options_arguments(parser)
    add_pipeline_arguments(parser)
    add_pipeline_positional_arguments(parser)


def add_pyav_parser(subparsers) -> None:
    # noinspection SpellCheckingInspection
    parser = subparsers.add_parser(name=CMD_PYAV, help=CMD_PYAV_HELP)
    assert isinstance(parser, ArgumentParser)
    add_ffmpeg_options_arguments(parser)
    add_pipeline_arguments(parser)
    add_pipeline_positional_arguments(parser)


def add_io_parser(subparsers) -> None:
    # noinspection SpellCheckingInspection
    parser = subparsers.add_parser(name=CMD_IO, help=CMD_IO_HELP)
    assert isinstance(parser, ArgumentParser)
    add_ffmpeg_options_arguments(parser)
    add_pipeline_arguments(parser)
    add_pipeline_positional_arguments(parser)


def add_rtsp_parser(subparsers) -> None:
    # noinspection SpellCheckingInspection
    parser = subparsers.add_parser(name=CMD_RTSP, help=CMD_RTSP_HELP)
    assert isinstance(parser, ArgumentParser)
    add_ffmpeg_options_arguments(parser)
    add_pipeline_arguments(parser)
    add_pipeline_positional_arguments(parser)


def default_argument_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog=PROG,
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=RawDescriptionHelpFormatter,
    )

    logging_group = parser.add_mutually_exclusive_group()
    logging_group.add_argument(
        "--colored-logging",
        "-c",
        action="store_true",
        default=False,
        help="Use colored logging",
    )
    logging_group.add_argument(
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

    parser.add_argument(
        __MODULE_PREFIX_FLAG,
        metavar="prefix",
        default=DEFAULT_MODULE_PREFIX,
        help=f"The prefix of the module (default: '{DEFAULT_MODULE_PREFIX}')",
    )

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
        "--use-static-ffmpeg",
        action="store_true",
        default=False,
        help="Use the binaries from the static-ffmpeg package",
    )
    parser.add_argument(
        "--use-uvloop",
        action="store_true",
        default=False,
        help="Replace the event loop with uvloop",
    )

    subparsers = parser.add_subparsers(dest="cmd")
    add_pixels_parser(subparsers)
    add_files_parser(subparsers)
    add_modules_parser(subparsers)
    add_list_parser(subparsers)
    add_inspect_parser(subparsers)
    add_pipe_parser(subparsers)
    add_pyav_parser(subparsers)
    add_io_parser(subparsers)
    add_rtsp_parser(subparsers)
    return parser


def get_default_arguments(
    cmdline: Optional[List[str]] = None,
    namespace: Optional[Namespace] = None,
) -> Namespace:
    parser = default_argument_parser()
    return parser.parse_known_args(cmdline, namespace)[0]
