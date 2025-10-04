import inspect
import logging
import sys
from typing import Literal

from loguru import logger

LogLevel = Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]

DEFAULT_TIME_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss:SSS}</green>"
DEFAULT_SOURCE_FORMAT = "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>"
DEFAULT_LEVEL_FORMAT = "<level>{level: <8}</level>"
DEFAULT_MESSAGE_FORMAT = "<level>{message}</level>"


# Intercept standard logging messages and route them to Loguru
# https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging
class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


def configure(*, level: LogLevel = "INFO", format: str | None = None) -> None:
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    chatty_packages: tuple[str] = ("scanner_scope",)
    if level in ("DEBUG",):
        for package in chatty_packages:
            logging.getLogger(package).setLevel("INFO")

    format = (
        format
        or f"{DEFAULT_TIME_FORMAT} | {DEFAULT_LEVEL_FORMAT} | {DEFAULT_SOURCE_FORMAT} - {DEFAULT_MESSAGE_FORMAT}"
    )
    logger.remove()
    # explicitly set colorize to True, since btq runs as part of a script inside the action
    # and the output is not recognized as a terminal
    logger.add(sys.stderr, colorize=True, level=level, format=format)
