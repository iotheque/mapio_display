import logging
import os


class LED:
    """Defines a led object"""

    def __init__(self, number: int, color: str) -> None:
        """Initialise led object

        Args:
            number (int): led number
            color (str): led color
        """
        self.logger = logging.getLogger(__name__)
        color = color.upper()

        if number in [1, 2, 3] and color in ["G", "R", "B"]:
            self.led_path = "/sys/class/leds/LED" + str(number) + "_" + color
        else:
            self.logger.error("Wrong led parameters")

    def on(self) -> None:
        """Set a led to ON"""
        try:
            os.system(f"echo 1 > {self.led_path}/brightness")  # nosec
        except AssertionError:
            self.logger.error("Unknown led")

    def off(self) -> None:
        """Set a led to OFF"""
        try:
            os.system(f"echo 0 > {self.led_path}/brightness")  # nosec
        except AssertionError:
            self.logger.error("Unknown led")
