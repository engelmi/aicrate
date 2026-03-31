import logging
import sys
import typing
from enum import IntEnum
from typing import Optional


class LogLevel(IntEnum):
    DEBUG = typing.cast(int, getattr(logging, "DEBUG"))
    INFO = typing.cast(int, getattr(logging, "INFO"))
    WARNING = typing.cast(int, getattr(logging, "WARNING"))
    ERROR = typing.cast(int, getattr(logging, "ERROR"))
    CRITICAL = typing.cast(int, getattr(logging, "CRITICAL"))

    @staticmethod
    def from_string(value: str) -> "LogLevel":
        valid_values = {
            "debug": LogLevel.DEBUG,
            "info": LogLevel.INFO,
            "warning": LogLevel.WARNING,
            "error": LogLevel.ERROR,
            "critical": LogLevel.CRITICAL,
        }
        if value.lower() in valid_values:
            return valid_values[value.lower()]
        raise KeyError(
            f"Unknown log level '{value}'. Has to be one of '{[k for k in valid_values.keys()]}'"
        )


logger = logging.getLogger("claudebox")


def configure_logger(
    lvl: LogLevel = LogLevel.WARNING, log_file: Optional[str] = None
) -> None:
    if logger.hasHandlers():
        return

    logger.setLevel(lvl)

    fmt = "%(asctime)s - %(levelname)s - %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt)

    handler = logging.StreamHandler(sys.stderr)
    if log_file is not None:
        handler = logging.FileHandler(log_file)
    handler.setLevel(lvl)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
