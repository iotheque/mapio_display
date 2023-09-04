import datetime
import logging
import os
import subprocess  # nosec
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any

import netifaces  # type: ignore
import netifaces as ni  # type: ignore
import psutil  # type: ignore
from gpiod import chip, line_request
from netifaces import AF_INET  # type: ignore
from PIL import Image, ImageDraw, ImageFont  # type: ignore

from mapio_display.epd.epd import EPD
from mapio_display.leds.leds import LED

SCREEN_REFRESH_PERIOD_S = 20


class MAPIO_CTRL(object):
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

        # ePaper control
        self.epd = EPD()
        self.views_list = ["HOME", "STATUS", "SYSTEM"]
        self.views_pool = deque(self.views_list)
        self.need_refresh = False
        self.current_view = self.views_pool[0]

        # Init ePaper
        self.epd.init()
        time.sleep(0.5)
        self.epd.displayPartBaseImage(self.get_current_buffered_image())

        # Leds control
        self.led_sys_green = LED(1, "G")
        self.led_sys_red = LED(1, "R")

    # ePaper methods
    def get_current_buffered_image(self, wait: bool = False) -> Image:
        """Get current image as buffered

        Args:
            wait (bool, optional): Indicates if wait message is printed. Defaults to False.

        Returns:
            Image: The buffered image
        """
        if self.current_view == "HOME":
            self.logger.info("HOME VIEW")
            image = self._generate_home_view(wait)
        elif self.current_view == "SYSTEM":
            image = self._generate_system_view(wait)
        elif self.current_view == "STATUS":
            image = self._generate_status_view(wait)

        return self.epd.getbuffer(image)

    def _generate_home_view(self, wait: bool) -> Image:
        """Generate the home view as an image

        Args:
            wait (bool): Indicates if wait message is printed

        Returns:
            Image: The home image
        """
        # Add logo
        img = Image.open(f"{Path(__file__).parent}/../images/mapio_logo_bw104x122.jpg")
        image = Image.new(
            "1", (self.epd.height, self.epd.width), 255
        )  # 255: clear the frame
        image.paste(img, (2, 2))

        # Add hour
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype("/usr/share/fonts/ttf/LiberationMono-Bold.ttf", 40)
        clock = datetime.datetime.now().strftime("%H:%M")
        draw.text((120, 2), clock, 0, font=font)

        # Wait rectangle
        draw.rectangle((190, 92, 245, 117), fill=255, outline="black")
        if wait:
            fontwait = ImageFont.truetype(
                "/usr/share/fonts/ttf/LiberationMono-Bold.ttf", 12
            )
            draw.text((194, 96), "Wait...", font=fontwait, fill=0)

        # Add version
        try:
            image_editable = ImageDraw.Draw(image)
            font = ImageFont.truetype(
                "/usr/share/fonts/ttf/LiberationMono-Bold.ttf", 12
            )
            os_version = Path("/etc/os-version").read_text()
        except:  # noqa: E722
            os_version = "None"
        image_editable.text((120, 90), "MAPIO OS: ", 0, font=font)
        image_editable.text((120, 105), os_version, 0, font=font)

        # Add IP address
        try:
            image_editable = ImageDraw.Draw(image)
            font = ImageFont.truetype(
                "/usr/share/fonts/ttf/LiberationMono-Bold.ttf", 12
            )
            def_gw_device = netifaces.gateways()["default"][netifaces.AF_INET][1]
            ip_addr = ni.ifaddresses(def_gw_device)[AF_INET][0]["addr"]
        except:  # noqa: E722
            ip_addr = "NO IP"
        image_editable.text((120, 70), ip_addr, 0, font=font)

        return image

    def _generate_system_view(self, wait: bool) -> Image:
        """Generate the system view as an image

        Args:
            wait (bool): Indicates if wait message is printed

        Returns:
            Image: The system image
        """
        font = ImageFont.truetype("/usr/share/fonts/ttf/LiberationMono-Bold.ttf", 28)
        image = Image.new("1", (self.epd.height, self.epd.width), 255)
        draw = ImageDraw.Draw(image)
        draw.text((0, 0), "System ", font=font, fill=0)

        font = ImageFont.truetype("/usr/share/fonts/ttf/LiberationMono-Bold.ttf", 15)
        draw.text((0, 30), f"•CPU: {psutil.cpu_percent()}%", font=font, fill=0)
        draw.text(
            (120, 30), f"•RAM: {psutil.virtual_memory().percent}%", font=font, fill=0
        )

        draw.text(
            (0, 50),
            f"•eMMC: {psutil.disk_usage('/usr/local').percent}%",
            font=font,
            fill=0,
        )
        uptime = os.popen(  # nosec
            "uptime | awk -F ',' '{print $1}' | cut -c14-"  # nosec
        ).read()  # nosec
        draw.text((120, 50), f"•Uptime: {uptime}", font=font, fill=0)

        battery_volt = os.popen("vcgencmd pmicrd 1d | awk '{print $3}'").read()  # nosec
        battery_volt_int = round(4 * int(battery_volt, 16) / 100) / 2

        draw.text((0, 70), f"•Battery: {battery_volt_int}V", font=font, fill=0)

        draw.text(
            (0, 90),
            f"•Temperature: {round(psutil.sensors_temperatures()['cpu_thermal'][0].current)}°C",
            font=font,
            fill=0,
        )

        draw.rectangle((190, 92, 245, 117), fill=255, outline="black")
        if wait:
            fontwait = ImageFont.truetype(
                "/usr/share/fonts/ttf/LiberationMono-Bold.ttf", 12
            )
            draw.text((194, 96), "Wait...", font=fontwait, fill=0)
        return image

    def _generate_status_view(self, wait: bool) -> Image:
        """Generate the status view as an image

        Args:
            wait (bool): Indicates if wait message is printed

        Returns:
            Image: The status image
        """
        font = ImageFont.truetype("/usr/share/fonts/ttf/LiberationMono-Bold.ttf", 15)
        image = Image.new("1", (self.epd.height, self.epd.width), 255)
        draw = ImageDraw.Draw(image)
        draw.line([(0, 40), (255, 40)])
        draw.line([(0, 80), (255, 80)])
        draw.text((0, 10), "Power", font=font, fill=0)
        if os.system("systemctl is-active --quiet docker.service") == 0:  # nosec
            draw.text((0, 90), "Docker    RUNNING", font=font, fill=0)
        else:
            draw.text((0, 90), "Docker    STOPPED", font=font, fill=0)

        command = ["ping", "-c", "1", "-W", "1", "google.fr"]
        if subprocess.call(command) == 0:  # nosec
            draw.text((0, 50), "Internet  CONNECTED", font=font, fill=0)
        else:
            draw.text((0, 50), "Internet  NOT CONNECTED", font=font, fill=0)

        if self.chg_chg_n.get_value() == 0:
            battery_volt = os.popen(  # nosec
                "vcgencmd pmicrd 1d | awk '{print $3}'"  # nosec
            ).read()  # nosec
            battery_volt_int = round(2 * int(battery_volt, 16) / 100)
            draw.text(
                (0, 10), f"Power     CHARGING ({battery_volt_int}V)", font=font, fill=0
            )
        elif self.chg_boost_n.get_value() == 0:
            draw.text((0, 10), "Power    ON BATTERY", font=font, fill=0)
        else:
            draw.text((0, 10), "Power     CHARGED", font=font, fill=0)

        # Wait rectangle
        draw.rectangle((190, 92, 245, 117), fill=255, outline="black")
        if wait:
            fontwait = ImageFont.truetype(
                "/usr/share/fonts/ttf/LiberationMono-Bold.ttf", 12
            )
            draw.text((194, 96), "Wait...", font=fontwait, fill=0)

        return image


# Create MAPIO control object
mapio_ctrl = MAPIO_CTRL()


def set_logger_for_tasks(logger: logging.Logger) -> None:
    """Set the logger used by MAPIO control object

    Args:
        logger (logging.Logger): Logger object
    """
    mapio_ctrl.logger = logger


def refresh_screen_task() -> None:
    """Task that refresh the epaper screen"""
    next_refresh_time = round(time.time())
    force_refresh = False
    mapio_ctrl.logger.info("Start refresh screen task")

    while True:
        if (next_refresh_time + SCREEN_REFRESH_PERIOD_S < round(time.time())) or (
            force_refresh is True
        ):
            next_refresh_time = round(time.time())
            force_refresh = False
            mapio_ctrl.logger.info("Refresh the screen")
            mapio_ctrl.epd.init()
            mapio_ctrl.epd.display(mapio_ctrl.get_current_buffered_image())

        elif mapio_ctrl.need_refresh:
            mapio_ctrl.logger.info("Short refresh of  the screen")
            mapio_ctrl.need_refresh = False
            force_refresh = True
            mapio_ctrl.epd.display_partial(
                mapio_ctrl.get_current_buffered_image(wait=True)
            )
            # Update view for next refresh
            mapio_ctrl.current_view = mapio_ctrl.views_pool[0]

        time.sleep(0.5)


def refresh_leds_task() -> None:
    """Task that refresh the leds"""
    logger = logging.getLogger(__name__)
    logger.info("Start refresh leds task")
    while True:
        # Check if docker service is running
        if os.system("systemctl is-active --quiet docker.service") == 0:  # nosec
            # led_sys_green.on()
            mapio_ctrl.led_sys_green.blink(500, 50)
            mapio_ctrl.led_sys_red.off()
        else:
            mapio_ctrl.led_sys_green.off()
            mapio_ctrl.led_sys_red.on()
    
        time.sleep(1)


def _gpio_chip_handler(buttons: Any) -> None:
    """Handler for GPIO buttons interrupts

    Args:
        buttons (List): List of GPIO that trigs the interrupt
    """
    while True:
        lines = buttons.event_wait(datetime.timedelta(seconds=10))
        if not lines.empty:
            for it in lines:
                event = it.event_read()
                mapio_ctrl.logger.info(f"Event: {event}")
                mapio_ctrl.logger.info(it.consumer)
                if it.consumer == "UP":
                    mapio_ctrl.need_refresh = True
                    mapio_ctrl.views_pool.rotate(-1)
                    mapio_ctrl.logger.info(f"next view is: {mapio_ctrl.views_pool[0]}")
                elif it.consumer == "DOWN":
                    mapio_ctrl.need_refresh = True
                    mapio_ctrl.views_pool.rotate(1)
                    mapio_ctrl.logger.info(f"next view is: {mapio_ctrl.views_pool[0]}")
                elif it.consumer == "MID":
                    mapio_ctrl.logger.info("MID has been pushed")
                else:
                    mapio_ctrl.logger.error("Unknown button")
        time.sleep(1)


def gpio_mon_create_task() -> None:
    """Task that manages the GPIO buttons"""
    mapio_ctrl.logger.info("Create GPIOs task")
    # Button mid on chip 0
    config = line_request()
    config.request_type = line_request.EVENT_FALLING_EDGE
    chip0 = chip(0)
    BUTTON_MID_LINE_OFFSETS = [18]
    buttons_mid = chip0.get_lines(BUTTON_MID_LINE_OFFSETS)
    for i in range(buttons_mid.size):
        config.consumer = "MID"
        buttons_mid[i].request(config)
    event = threading.Thread(target=_gpio_chip_handler, args=(buttons_mid,))
    event.start()

    # Button up and down on chip 1
    config = line_request()
    config.request_type = line_request.EVENT_FALLING_EDGE
    chip1 = chip(1)
    BUTTON_UP_DOWN_LINE_OFFSETS = [0, 1]
    buttons_up_down = chip1.get_lines(BUTTON_UP_DOWN_LINE_OFFSETS)
    for i in range(buttons_up_down.size):
        if i == 0:
            config.consumer = "DOWN"
        else:
            config.consumer = "UP"
        buttons_up_down[i].request(config)
    event = threading.Thread(target=_gpio_chip_handler, args=(buttons_up_down,))
    event.start()
