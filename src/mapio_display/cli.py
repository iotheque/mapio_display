"""Console script for mapio_display."""

# Standard lib imports
import logging
import logging.config
import sys
import threading
import time
from pathlib import Path
from typing import Optional

# Third-party lib imports
import click  # type: ignore

from mapio_display.app.app import (
    gpio_mon_create_task,
    refresh_leds_task,
    refresh_screen_task,
    set_logger_for_tasks,
)
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
    """App function for MAPIO ."""
    logger = logging.getLogger(__name__)
    logger.info("Start screen")

    set_logger_for_tasks(logger)
    event = threading.Thread(target=refresh_screen_task)
    event.start()

    event = threading.Thread(target=refresh_leds_task)
    event.start()

    gpio_mon_create_task()

    while True:
        # Nothing to do, just wait
        time.sleep(10)


@main.command()
def reset() -> None:
    """Reset epaper."""
    logger = logging.getLogger(__name__)
    logger.info("Reset screen")

    epd = EPD()
    epd.init()
    epd.clear(0xFF)


if __name__ == "__main__":
    sys.exit(main())
