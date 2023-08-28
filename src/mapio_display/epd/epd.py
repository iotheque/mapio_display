#!/usr/bin/python
# -*- coding:utf-8 -*-
import logging
import time
from typing import Any

import gpiod  # type: ignore
import spidev  # type: ignore
from PIL import Image  # type: ignore

# Display resolution
EPD_WIDTH = 122
EPD_HEIGHT = 250

# Pin definition
RST_PIN = 13
DC_PIN = 14
BUSY_PIN = 12


def epd_delay_ms(delaytime: int) -> None:
    """Utility function to create a delay in ms

    Args:
        delaytime (int): Wait delay in ms
    """
    time.sleep(delaytime / 1000.0)


class EPD:
    """Initialize a epaper class screen"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)

    lut_partial_update = [
        0x0,
        0x40,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x80,
        0x80,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x40,
        0x40,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x80,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x14,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x1,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x1,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x22,
        0x22,
        0x22,
        0x22,
        0x22,
        0x22,
        0x0,
        0x0,
        0x0,
        0x22,
        0x17,
        0x41,
        0x00,
        0x32,
        0x36,
    ]

    lut_full_update = [
        0x80,
        0x4A,
        0x40,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x40,
        0x4A,
        0x80,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x80,
        0x4A,
        0x40,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x40,
        0x4A,
        0x80,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0xF,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0xF,
        0x0,
        0x0,
        0xF,
        0x0,
        0x0,
        0x2,
        0xF,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x1,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x0,
        0x22,
        0x22,
        0x22,
        0x22,
        0x22,
        0x22,
        0x0,
        0x0,
        0x0,
        0x22,
        0x17,
        0x41,
        0x0,
        0x32,
        0x36,
    ]

    def spi_transfer(self, data: Any) -> None:
        """Write bytes on SPI bus

        Args:
            data (Any): Data to send on SPI
        """
        self.spi.writebytes(data)

    def reset(self) -> None:
        """Reset EPD"""
        self.reset_gpio.set_value(1)
        epd_delay_ms(20)
        self.reset_gpio.set_value(0)
        epd_delay_ms(2)
        self.reset_gpio.set_value(1)
        epd_delay_ms(20)

    def send_command(self, command: Any) -> None:
        """Send a command on EPD

        Args:
            command (Any): Send a command on EPD (see EPD datasheet for more details)
        """
        self.dc_gpio.set_value(0)
        self.spi_transfer([command])

    def send_data(self, data: Any) -> None:
        """Send data on EPD

        Args:
            command (Any): Send data on EPD (see EPD datasheet for more details)
        """
        self.dc_gpio.set_value(1)
        self.spi_transfer([data])

    def wait_busy(self) -> None:
        """Wait EPD ready state"""
        self.logger.debug("e-Paper busy")
        while self.busy_gpio.get_value() == 1:  # 0: idle, 1: busy
            epd_delay_ms(10)
        self.logger.debug("e-Paper busy release")

    def turn_on_display(self) -> None:
        """Turn ON EPD"""
        self.send_command(0x22)  # Display Update Control
        self.send_data(0xC7)
        self.send_command(0x20)  # Activate Display Update Sequence
        self.wait_busy()

    def turn_on_display_part(self) -> None:
        """Turn ON EPD"""
        self.send_command(0x22)  # Display Update Control
        self.send_data(0x0F)  # fast:0x0c, quality:0x0f, 0xcf
        self.send_command(0x20)  # Activate Display Update Sequence
        self.wait_busy()

    def Lut(self, lut: Any) -> None:
        """Send lut data and configuration

        Args:
            lut (Any): lut data
        """
        self.send_command(0x32)
        for i in range(0, 153):
            self.send_data(lut[i])
        self.wait_busy()

    def set_lut(self, lut: Any) -> None:
        """Send lut data and configuration

        Args:
            lut (Any): lut data
        """
        self.Lut(lut)
        self.send_command(0x3F)
        self.send_data(lut[153])
        self.send_command(0x03)  # gate voltage
        self.send_data(lut[154])
        self.send_command(0x04)  # source voltage
        self.send_data(lut[155])  # VSH
        self.send_data(lut[156])  # VSH2
        self.send_data(lut[157])  # VSL
        self.send_command(0x2C)  # VCOM
        self.send_data(lut[158])

    def set_window(self, x_start: int, y_start: int, x_end: int, y_end: int) -> None:
        """Setting the display window

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
        """_summary_

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
        """Initialize the e-Paper register"""
        chip = gpiod.chip(0)
        config = gpiod.line_request()
        config.request_type = gpiod.line_request.DIRECTION_OUTPUT

        self.reset_gpio = chip.get_line(RST_PIN)
        self.dc_gpio = chip.get_line(DC_PIN)
        self.reset_gpio.request(config)
        self.dc_gpio.request(config)

        config.request_type = gpiod.line_request.DIRECTION_INPUT
        self.busy_gpio = chip.get_line(BUSY_PIN)
        self.busy_gpio.request(config)

        # EPD hardware init start
        self.reset()

        self.wait_busy()
        self.send_command(0x12)  # SWRESET
        self.wait_busy()

        self.send_command(0x01)  # Driver output control
        self.send_data(0xF9)
        self.send_data(0x00)
        self.send_data(0x00)

        self.send_command(0x11)  # data entry mode
        self.send_data(0x03)

        self.set_window(0, 0, self.width - 1, self.height - 1)
        self.SetCursor(0, 0)

        self.send_command(0x3C)
        self.send_data(0x05)

        self.send_command(0x21)  # Display update control
        self.send_data(0x00)
        self.send_data(0x80)

        self.send_command(0x18)
        self.send_data(0x80)

        self.wait_busy()

        self.set_lut(self.lut_full_update)

    def getbuffer(self, image: Image) -> Any:
        """Generate a buffer based on an Image

        Args:
            image (Image): The image to transform in buffer

        Returns:
            Any: Generated buffer
        """
        img = image
        imwidth, imheight = img.size
        self.logger.info(f"imwidth {imwidth}, imheight {imheight}")
        if imwidth == self.width and imheight == self.height:
            img = img.convert("1")
        elif imwidth == self.height and imheight == self.width:
            # image has correct dimensions, but needs to be rotated
            img = img.rotate(90, expand=True).convert("1")
        else:
            self.logger.warning(
                "Wrong image dimensions: must be "
                + str(self.width)
                + "x"
                + str(self.height)
            )
            # return a blank buffer
            return [0x00] * (int(self.width / 8) * self.height)

        buf = bytearray(img.tobytes("raw"))
        return buf

    def display(self, image: bytearray) -> None:
        """Send and display the data on the screen

        Args:
            image (bytearray): Data to send to screen
        """
        if self.width % 8 == 0:
            linewidth = int(self.width / 8)
        else:
            linewidth = int(self.width / 8) + 1

        self.send_command(0x24)
        for j in range(0, self.height):
            for i in range(0, linewidth):
                self.send_data(image[i + j * linewidth])
        self.turn_on_display()

    def display_partial(self, image: bytearray) -> None:
        """Send the data on the screen and execute a partial refresh

        Args:
            image (bytearray): Data to send to screen
        """
        if self.width % 8 == 0:
            linewidth = int(self.width / 8)
        else:
            linewidth = int(self.width / 8) + 1

        self.reset_gpio.set_value(0)
        epd_delay_ms(1)
        self.reset_gpio.set_value(1)

        self.set_lut(self.lut_partial_update)
        self.send_command(0x37)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x40)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)

        self.send_command(0x3C)  # BorderWavefrom
        self.send_data(0x80)

        self.send_command(0x22)
        self.send_data(0xC0)
        self.send_command(0x20)
        self.wait_busy()

        self.set_window(0, 0, self.width - 1, self.height - 1)
        self.SetCursor(0, 0)

        self.send_command(0x24)  # WRITE_RAM
        for j in range(0, self.height):
            for i in range(0, linewidth):
                self.send_data(image[i + j * linewidth])
        self.turn_on_display_part()

    def displayPartBaseImage(self, image: bytearray) -> None:
        """Refresh a base image

        Args:
            image (bytearray): the raw image to send
        """
        if self.width % 8 == 0:
            linewidth = int(self.width / 8)
        else:
            linewidth = int(self.width / 8) + 1

        self.send_command(0x24)
        for j in range(0, self.height):
            for i in range(0, linewidth):
                self.send_data(image[i + j * linewidth])

        self.send_command(0x26)
        for j in range(0, self.height):
            for i in range(0, linewidth):
                self.send_data(image[i + j * linewidth])
        self.turn_on_display()

    def clear(self, color: int) -> None:
        """Clear all the screen with specific color

        Args:
            color (int): Data to send to screen
        """
        if self.width % 8 == 0:
            linewidth = int(self.width / 8)
        else:
            linewidth = int(self.width / 8) + 1

        self.send_command(0x24)
        for j in range(0, self.height):
            for i in range(0, linewidth):
                self.send_data(color)

        self.turn_on_display()

    def enter_deep_sleep(self) -> None:
        """Set display in deep sleep mode"""
        self.send_command(0x10)  # enter deep sleep
        self.send_data(0x01)
        epd_delay_ms(2000)

        self.reset_gpio.release()
        self.dc_gpio.release()
        self.busy_gpio.release()
