"""Console script for mapio_display."""

# Standard lib imports
import logging
import logging.config
import sys
import time
from pathlib import Path
from typing import Optional

# Third-party lib imports
import click  # type: ignore

from mapio_display.app.app import mapio_refresh_main_screen
from mapio_display.epd.epd import EPD

# Local package imports


# Define this function as a the main command entrypoint
@click.group()
# Create an argument that expects a path to a valid file
@click.option(
    "--log-config",
    help="Path to the log config file",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=False,
        readable=True,
        resolve_path=True,
    ),
)
# Display the help if no option is provided
@click.help_option()
def main(
    log_config: Optional[str],
) -> None:
    """Console script for mapio_display."""
    if log_config is not None:
        logging.config.fileConfig(log_config)
    else:
        # Default to some basic config
        log_config = f"{Path(__file__).parent}/log.cfg"
        logging.config.fileConfig(log_config)
        tmp_logger = logging.getLogger(__name__)
        tmp_logger.warning("No log config provided, using default configuration")
    logger = logging.getLogger(__name__)
    logger.info("Logger initialized")


@main.command()
def app() -> None:
    logger = logging.getLogger((__name__))
    logger.info("Start screen")

    epd = EPD()
    epd.init()
    epd.clear(0xFF)
    epd.enter_deep_sleep()

    while True:
        mapio_refresh_main_screen(epd)
        time.sleep(10)


@main.command()
def reset() -> None:
    logger = logging.getLogger((__name__))
    logger.info("Reset screen")

    epd = EPD()
    epd.init()
    epd.clear(0xFF)


if __name__ == "__main__":
    sys.exit(main())
