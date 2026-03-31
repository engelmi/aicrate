import sys
import traceback
from typing import Sequence

from claudebox.cli import parse_arguments
from claudebox.logger import LogLevel, configure_logger, logger


def main(args: Sequence[str] = None):
    try:
        cli_args, parser = parse_arguments(args)
        configure_logger(cli_args.log_level, getattr(cli_args, "log_file", None))

        if not cli_args.subcommand:
            logger.error("Subcommand required")
            parser.print_usage()
            return

        cli_args.func(cli_args)
    except Exception as ex:
        logger.error(f"Running claudebox failed: {ex}")
        if logger.level == LogLevel.DEBUG:
            traceback.print_exc()
        sys.exit(1)
