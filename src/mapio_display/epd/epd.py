"""MAPIO epaper control."""

#!/usr/bin/python
import time
from typing import Any

import gpiod  # type: ignore
import spidev  # type: ignore
from loguru import logger
from PIL import Image  # type: ignore

# Display resolution
EPD_WIDTH = 122
EPD_HEIGHT = 250

# Pin definition
RST_PIN = 13
DC_PIN = 14
BUSY_PIN = 12


def epd_delay_ms(delaytime: int) -> None:
    """Utility function to create a delay in ms.

    Args:
        delaytime (int): Wait delay in ms
    """
    time.sleep(delaytime / 1000.0)


class EPD:
    """Initialize a epaper class screen."""

    def __init__(self) -> None:
        """Initialise epaper."""
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        self.spi: Any = spidev.SpiDev()  # type: ignore
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 4000000

        chip = gpiod.chip(1)
        config = gpiod.line_request()
        config.request_type = gpiod.line_request.DIRECTION_OUTPUT

        self.reset_gpio = chip.get_line(RST_PIN)
        self.dc_gpio = chip.get_line(DC_PIN)
        self.reset_gpio.request(config)
        self.dc_gpio.request(config)

        config.request_type = gpiod.line_request.DIRECTION_INPUT
        self.busy_gpio = chip.get_line(BUSY_PIN)
        self.busy_gpio.request(config)
        self.is_busy = False
        logger.info("EPD initialized")

    def spi_transfer(self, data: Any) -> None:
        """Write bytes on SPI bus.

        Args:
            data (Any): Data to send on SPI
        """
        self.spi.writebytes2(data)

    def reset(self) -> None:
        """Reset EPD."""
        self.reset_gpio.set_value(1)
        epd_delay_ms(20)
        self.reset_gpio.set_value(0)
        epd_delay_ms(10)
        self.reset_gpio.set_value(1)
        epd_delay_ms(20)

    def send_command(self, command: Any) -> None:
        """Send a command on EPD.

        Args:
            command (Any): Send a command on EPD (see EPD datasheet for more details)
        """
        self.dc_gpio.set_value(0)
        self.spi_transfer([command])

    def send_data(self, data: Any) -> None:
        """Send data on EPD.

        Args:
            data (Any): Send data on EPD (see EPD datasheet for more details)
        """
        self.dc_gpio.set_value(1)
        self.spi_transfer([data])

    # send a lot of data
    def send_data2(self, data: Any) -> None:
        """Send data on EPD.

        Args:
            data (Any): Send a raw data on EPD (see EPD datasheet for more details)
        """
        self.dc_gpio.set_value(1)
        self.spi_transfer(data)

    def wait_busy(self) -> bool:
        """Wait EPD ready state."""
        start_time = time.time()

        while self.busy_gpio.get_value() == 1:  # 0: idle, 1: busy
            if time.time() - start_time > 6:
                logger.error("Timeout occurred while waiting for e-Paper to become ready")
                return False
            epd_delay_ms(10)
        self.is_busy = False
        return True

    def turn_on_display(self) -> bool:
        """Turn ON EPD."""
        self.send_command(0x22)  # Display Update Control
        self.send_data(0xF7)
        self.send_command(0x20)  # Activate Display Update Sequence
        return self.wait_busy()

    def set_window(self, x_start: int, y_start: int, x_end: int, y_end: int) -> None:
        """Setting the display window.

        Args:
            x_start (int): _description_
            y_start (int): _description_
            x_end (int): _description_
            y_end (int): _description_
        """
        self.send_command(0x44)  # SET_RAM_X_ADDRESS_START_END_POSITION
        # x point must be the multiple of 8 or the last 3 bits will be ignored
        self.send_data((x_start >> 3) & 0xFF)
        self.send_data((x_end >> 3) & 0xFF)

        self.send_command(0x45)  # SET_RAM_Y_ADDRESS_START_END_POSITION
        self.send_data(y_start & 0xFF)
        self.send_data((y_start >> 8) & 0xFF)
        self.send_data(y_end & 0xFF)
        self.send_data((y_end >> 8) & 0xFF)

    def SetCursor(self, x: int, y: int) -> None:
        """SetCursor on the screen.

        Args:
            x (int): X-axis starting position
            y (int): Y-axis starting position
        """
        self.send_command(0x4E)  # SET_RAM_X_ADDRESS_COUNTER
        # x point must be the multiple of 8 or the last 3 bits will be ignored
        self.send_data(x & 0xFF)

        self.send_command(0x4F)  # SET_RAM_Y_ADDRESS_COUNTER
        self.send_data(y & 0xFF)
        self.send_data((y >> 8) & 0xFF)

    def init(self) -> None:
        """Initialize the e-Paper register."""
        # EPD hardware init start
        self.reset()

        self.wait_busy()
        self.send_command(0x12)  # SWRESET
        epd_delay_ms(10)

        self.send_command(0x01)  # Driver output control
        self.send_data(0xF9)
        self.send_data(0x00)
        self.send_data(0x00)

        self.send_command(0x11)  # data entry mode Source from S8 to S167
        self.send_data(0x03)

        self.set_window(0, 0, self.width - 1, self.height - 1)

        self.send_command(0x3C)
        self.send_data(0x05)

        self.send_command(0x18)
        self.send_data(0x80)

        self.send_command(0x21)  # Normal RAM,
        self.send_data(0x00)
        self.send_data(0x80)

        self.wait_busy()

    def getbuffer(self, image: Image.Image) -> Any:
        """Generate a buffer based on an Image.

        Args:
            image (Image): The image to transform in buffer

        Returns:
            Any: Generated buffer
        """
        # Rotate the image because screen is placed at 180°
        img = image.rotate(180)

        imwidth, imheight = img.size
        logger.debug(f"imwidth {imwidth}, imheight {imheight}")
        if imwidth == self.width and imheight == self.height:
            img = img.convert("1")
        elif imwidth == self.height and imheight == self.width:
            # image has correct dimensions, but needs to be rotated
            img = img.rotate(90, expand=True).convert("1")
        else:
            logger.warning(
                "Wrong image dimensions: must be " + str(self.width) + "x" + str(self.height)
            )
            # return a blank buffer
            return [0x00] * (int(self.width / 8) * self.height)

        return bytearray(img.tobytes())  # type: ignore

    def display(self, image: bytearray) -> bool:
        """Send and display the data on the screen.

        Args:
            image (bytearray): Data to send to screen
        """
        self.send_command(0x24)
        self.send_data2(image)
        is_ok = self.turn_on_display()
        self.enter_deep_sleep()
        return is_ok

    def displayPartBaseImage(self, image: Image.Image) -> None:
        """Refresh a base image.

        Args:
            image (Image): the raw image to send
        """
        self.send_command(0x24)
        self.send_data2(image)

        self.send_command(0x26)
        self.send_data2(image)
        self.turn_on_display()

    def clear(self, color: int) -> None:
        """Clear all the screen with specific color.

        Args:
            color (int): Data to send to screen
        """
        if self.width % 8 == 0:
            linewidth = int(self.width / 8)
        else:
            linewidth = int(self.width / 8) + 1

        self.send_command(0x24)
        self.send_data2([color] * int(self.height * linewidth))
        self.turn_on_display()

    def enter_deep_sleep(self) -> None:
        """Set display in deep sleep mode."""
        self.send_command(0x10)  # enter deep sleep
