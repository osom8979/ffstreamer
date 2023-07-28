# -*- coding: utf-8 -*-

from sys import exit as sys_exit
from typing import Callable, List, Optional

from ffstreamer.apps.files import files_main
from ffstreamer.apps.inspect import inspect_main
from ffstreamer.apps.modules import modules_main
from ffstreamer.apps.pipe import pipe_main
from ffstreamer.apps.pixels import pixels_main
from ffstreamer.apps.pyav import pyav_main
from ffstreamer.arguments import (
    CMD_FILES,
    CMD_INSPECT,
    CMD_LIST,
    CMD_MODULES,
    CMD_PIPE,
    CMD_PIXELS,
    CMD_PYAV,
    CMDS,
    get_default_arguments,
)
from ffstreamer.ffmpeg.static_lib import StaticFFmpegPaths
from ffstreamer.logging.logging import (
    SEVERITY_NAME_DEBUG,
    logger,
    set_colored_formatter_logging_config,
    set_root_level,
    set_simple_logging_config,
)


def main(
    cmdline: Optional[List[str]] = None,
    printer: Callable[..., None] = print,
) -> int:
    args = get_default_arguments(cmdline)

    if not args.cmd:
        printer("The command does not exist")
        return 1

    cmd = args.cmd
    colored_logging = args.colored_logging
    simple_logging = args.simple_logging
    severity = args.severity
    debug = args.debug
    verbose = args.verbose

    assert cmd in CMDS
    assert isinstance(colored_logging, bool)
    assert isinstance(simple_logging, bool)
    assert isinstance(severity, str)
    assert isinstance(debug, bool)
    assert isinstance(verbose, int)

    if colored_logging:
        set_colored_formatter_logging_config()
    elif simple_logging:
        set_simple_logging_config()

    if debug:
        set_root_level(SEVERITY_NAME_DEBUG)
    else:
        set_root_level(severity)

    logger.debug(f"Arguments: {args}")

    assert isinstance(args.module_prefix, str)
    assert isinstance(args.ffmpeg_path, str)
    assert isinstance(args.ffprobe_path, str)
    assert isinstance(args.use_static_ffmpeg, bool)

    static_lib = StaticFFmpegPaths()
    if args.use_static_ffmpeg:
        static_lib.open()
        args.ffmpeg_path = static_lib.ffmpeg_path
        args.ffprobe_path = static_lib.ffprobe_path
        logger.debug(f"Use static ffmpeg binary: '{args.ffmpeg_path}'")
        logger.debug(f"Use static ffprobe binary: '{args.ffprobe_path}'")

    try:
        if cmd == CMD_FILES:
            return files_main(args, printer=printer)
        elif cmd == CMD_INSPECT:
            return inspect_main(args, printer=printer)
        elif cmd in (CMD_LIST, CMD_MODULES):
            return modules_main(args, printer=printer)
        elif cmd == CMD_PIPE:
            return pipe_main(args, printer=printer)
        elif cmd == CMD_PIXELS:
            return pixels_main(args, printer=printer)
        elif cmd == CMD_PYAV:
            return pyav_main(args, printer=printer)
        else:
            assert False, "Inaccessible section"
    except BaseException as e:
        logger.exception(e)
        return 1
    finally:
        if static_lib.entered:
            static_lib.close()


if __name__ == "__main__":
    sys_exit(main())
