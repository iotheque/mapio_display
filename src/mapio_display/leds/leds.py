"""MAPIO leds controls."""

from pathlib import Path

from loguru import logger


class LED:
    """Defines a led object."""

    def __init__(self, number: int, color: str) -> None:
        """Initialise led object.

        Args:
            number (int): led number
            color (str): led color
        """
        color = color.upper()
        self.number = number

        if number in [1, 2, 3] and color in ["G", "R", "B"]:
            self.led_path = "/sys/class/leds/LED" + str(number) + "_" + color
        else:
            logger.warning("Wrong led parameters")

    def on(self) -> None:
        """Set a led to ON."""
        try:
            with Path.open(Path(f"{self.led_path}/brightness"), "w") as brightness:
                brightness.write("1")
        except OSError:
            logger.warning("Unknown led")

    def off(self) -> None:
        """Set a led to OFF."""
        try:
            with Path.open(Path(f"{self.led_path}/brightness"), "w") as brightness:
                brightness.write("0")
        except OSError:
            logger.warning("Unknown led")

    def blink(self, start: bool) -> None:
        """Make a led blinking."""
        try:
            with Path.open(Path(f"{self.led_path}/trigger"), "w") as trigger:
                if start:
                    trigger.write("timer")
                else:
                    trigger.write("none")
            if start:
                with Path.open(Path(f"{self.led_path}/delay_on"), "w") as timer_on:
                    timer_on.write("100")
                with Path.open(Path(f"{self.led_path}/delay_off"), "w") as timer_off:
                    timer_off.write("100")

        except OSError:
            logger.warning("Unknown led")

    def reset(self, number: int) -> None:
        """Reset all color for a specific led."""
        try:
            for color in ["R", "G", "B"]:
                path = "/sys/class/leds/LED" + str(number) + "_" + color + "/brightness"
                with Path.open(Path(path), "w") as led:
                    led.write("0")
                path = "/sys/class/leds/LED" + str(number) + "_" + color + "/trigger"
                with Path.open(Path(path), "w") as led:
                    led.write("none")
        except OSError:
            logger.warning("Unknown led")
