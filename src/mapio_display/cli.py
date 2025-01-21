"""Console script for mapio_display."""

# Standard lib imports
import sys
import threading
import time

# Third-party lib imports
import click  # type: ignore
from loguru import logger

from mapio_display.app.app import (
    gpio_mon_create_task,
    mapio_ctrl,
    refresh_leds_task,
    refresh_screen_task,
)

# Local package imports


# Define this function as a the main command entrypoint
@click.group()
# Create an argument that expects a path to a valid file
@click.option(
    "-v",
    "--verbose",
    help="Verbose mode",
    count=True,
)
# Display the help if no option is provided
@click.help_option("-h", "--help")
def main(
    verbose: int,
) -> None:
    """Console script for mapio_display."""
    """Console script for interactivepath."""
    # Set the log level if required
    if verbose == 0:
        logger.remove()
        logger.add(sys.stderr, level="INFO")


@main.command()
def app() -> None:
    """App function for MAPIO ."""
    logger.info("Start screen")

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
    logger.info("Reset screen")

    mapio_ctrl.epd.init()
    mapio_ctrl.epd.clear(0xFF)


if __name__ == "__main__":
    sys.exit(main())
