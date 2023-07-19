# -*- coding: utf-8 -*-

from asyncio import StreamReader
from asyncio.exceptions import CancelledError
from logging import Logger


async def logging_stream(
    name: str,
    reader: StreamReader,
    logger: Logger,
    level: int,
) -> None:
    try:
        logger.debug(f"Stream[{name}] start reading ...")
        while not reader.at_eof():
            try:
                buff = await reader.readline()
            except ValueError:
                logger.warning(f"Stream[{name}] limit is reached")
            else:
                line = str(buff, encoding="utf-8").rstrip()
                logger.log(level, line)
    except CancelledError:
        logger.debug(f"Stream[{name}] is cancelled")
    except BaseException as unknown_error:
        logger.exception(unknown_error)
    finally:
        logger.debug(f"Stream[{name}] read finished.")
