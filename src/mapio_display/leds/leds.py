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
        self.number = number

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

    def blink(self, period_ms: int, duty_cyle: int) -> None:
        """Make a led blinking

        Args:
            period_ms (int): Blink period ms
            duty_cyle (int): Duty cycle in percent
        """
        try:
            os.system(f"echo timer > {self.led_path}/trigger")  # nosec
            os.system(  # nosec
                f"echo {round(period_ms * duty_cyle / 100)} > {self.led_path}/delay_on"  # nosec
            )  # nosec
            os.system(  # nosec
                f"echo {round(period_ms * (100 - duty_cyle) / 100)} \
                    > {self.led_path}/delay_off"  # nosec
            )  # nosec

        except AssertionError:
            self.logger.error("Unknown led")

    def reset(self, number: int) -> None:
        """Reset all color for a specific led"""
        try:
            for color in ["R", "G", "B"]:
                path = "/sys/class/leds/LED" + str(number) + "_" + color
                os.system(f"echo 0 > {path}/brightness")  # nosec
        except AssertionError:
            self.logger.error("Unknown led")
