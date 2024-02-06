import datetime
import logging
import os
import random
import string
import subprocess  # nosec
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any, Tuple

import gpiod
import netifaces  # type: ignore
import netifaces as ni  # type: ignore
import psutil  # type: ignore
import qrcode  # type: ignore
from gpiod import chip, line_request
from netifaces import AF_INET  # type: ignore
from PIL import Image, ImageDraw, ImageFont  # type: ignore

from mapio_display.epd.epd import EPD
from mapio_display.leds.leds import LED

SCREEN_REFRESH_PERIOD_S = 60


class MAPIO_CTRL(object):
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

        # ePaper control
        self.epd = EPD()
        self.views_list = ["HOME", "STATUS", "SETUP", "SYSTEM"]
        # check if there is a custom image to print
        if os.path.exists("/usr/local/homeassistant/media/epaper.jpg"):
            self.views_list.append("CUSTOM")
        self.views_pool = deque(self.views_list)
        self.need_refresh = False
        self.current_view = self.views_pool[0]
        self.mid_press = False

        # ePaper Fonts
        font_path = "/usr/share/fonts/ttf/LiberationMono-Bold.ttf"
        self.font12 = ImageFont.truetype(font_path, 12)
        self.font15 = ImageFont.truetype(font_path, 15)
        self.font28 = ImageFont.truetype(font_path, 28)
        self.font40 = ImageFont.truetype(font_path, 40)

        # Init ePaper
        self.epd.init()
        time.sleep(0.5)
        self.epd.displayPartBaseImage(self.get_current_buffered_image())

        # Leds control
        self.led_sys_green = LED(1, "G")
        self.led_sys_red = LED(1, "R")
        self.led_chg_green = LED(3, "G")
        self.led_chg_red = LED(3, "R")
        self.all_leds = [
            self.led_sys_green,
            self.led_sys_red,
            self.led_chg_green,
            self.led_chg_red,
        ]
        for led in self.all_leds:
            led.off()
            led.logger = self.logger

        # GPIOs for charger control
        chip = gpiod.chip(1)
        config = gpiod.line_request()
        config.request_type = gpiod.line_request.DIRECTION_INPUT
        config.flags = gpiod.line_request.FLAG_BIAS_PULL_UP
        self.chg_chg_n = chip.get_line(8)
        self.chg_chg_n.request(config)
        self.chg_acok_n = chip.get_line(9)
        self.chg_acok_n.request(config)
        self.chg_boost_n = chip.get_line(10)
        self.chg_boost_n.request(config)

        # Access point
        self.wifi_passwd = ""

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
        elif self.current_view == "SETUP":
            image = self._generate_setup_view(wait)
        elif self.current_view == "CUSTOM":
            image = self._generate_custom_view(wait)

        return self.epd.getbuffer(image)

    def _generate_custom_view(self, wait: bool) -> Image:
        """Generate the custom view as an image

        Args:
            wait (bool): Indicates if wait message is printed

        Returns:
            Image: The custom view
        """
        image = Image.new(
            "1", (self.epd.height, self.epd.width), 255
        )  # 255: clear the frame
        if os.path.exists("/usr/local/homeassistant/media/epaper.jpg"):
            img = Image.open("/usr/local/homeassistant/media/epaper.jpg")
            self.logger.info("Returns custom image")
            image.paste(img, (0, 0))
            return image
        return image

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
        clock = datetime.datetime.now().strftime("%H:%M")
        draw.text((120, 2), clock, 0, font=self.font40)

        # Wait rectangle
        self._draw_wait_rectangle(wait, draw)

        # Add version
        try:
            image_editable = ImageDraw.Draw(image)
            os_version = os.popen(  # nosec
                "cat /etc/os-release | grep PRETTY_NAME | awk '{print $4}'"  # nosec
            ).read()  # nosec
        except:  # noqa: E722
            os_version = "None"
        image_editable.text((120, 90), "MAPIO OS: ", 0, font=self.font12)
        image_editable.text((120, 105), os_version, 0, font=self.font12)

        # Add IP address
        try:
            image_editable = ImageDraw.Draw(image)
            def_gw_device = netifaces.gateways()["default"][netifaces.AF_INET][1]
            ip_addr = ni.ifaddresses(def_gw_device)[AF_INET][0]["addr"]
        except:  # noqa: E722
            ip_addr = "NO IP"
        image_editable.text((120, 70), ip_addr, 0, font=self.font12)

        return image

    def _generate_system_view(self, wait: bool) -> Image:
        """Generate the system view as an image

        Args:
            wait (bool): Indicates if wait message is printed

        Returns:
            Image: The system image
        """
        image = Image.new("1", (self.epd.height, self.epd.width), 255)
        draw = ImageDraw.Draw(image)
        draw.text((0, 0), "System ", font=self.font28, fill=0)

        draw.text((0, 30), f"•CPU: {psutil.cpu_percent()}%", font=self.font15, fill=0)
        draw.text(
            (120, 30),
            f"•RAM: {psutil.virtual_memory().percent}%",
            font=self.font15,
            fill=0,
        )

        draw.text(
            (0, 50),
            f"•eMMC: {psutil.disk_usage('/usr/local').percent}%",
            font=self.font15,
            fill=0,
        )
        uptime = os.popen(  # nosec
            "uptime | awk -F ',' '{print $1}' | cut -c14-"  # nosec
        ).read()  # nosec
        draw.text((120, 50), f"•Uptime: {uptime}", font=self.font15, fill=0)

        battery_volt, _ = self._get_battery_voltage()
        draw.text((0, 70), f"•Battery: {battery_volt}V", font=self.font15, fill=0)

        draw.text(
            (0, 90),
            f"•Temperature: {round(psutil.sensors_temperatures()['cpu_thermal'][0].current)}°C",
            font=self.font15,
            fill=0,
        )

        # Wait rectangle
        self._draw_wait_rectangle(wait, draw)

        return image

    def _generate_status_view(self, wait: bool) -> Image:
        """Generate the status view as an image

        Args:
            wait (bool): Indicates if wait message is printed

        Returns:
            Image: The status image
        """
        image = Image.new("1", (self.epd.height, self.epd.width), 255)
        draw = ImageDraw.Draw(image)
        draw.line([(0, 40), (255, 40)])
        draw.line([(0, 80), (255, 80)])
        draw.text((0, 10), "Power", font=self.font15, fill=0)
        if os.system("systemctl is-active --quiet docker.service") == 0:  # nosec
            draw.text((0, 90), "Docker    RUNNING", font=self.font15, fill=0)
        else:
            draw.text((0, 90), "Docker    STOPPED", font=self.font15, fill=0)

        if self._send_ping_command():
            draw.text((0, 50), "Internet  CONNECTED", font=self.font15, fill=0)
        else:
            draw.text((0, 50), "Internet  NOT CONNECTED", font=self.font15, fill=0)

        if self.chg_chg_n.get_value() == 0:
            _, percent = self._get_battery_voltage()
            draw.text(
                (0, 10), f"Power     CHARGING ({percent}%)", font=self.font15, fill=0
            )
        elif self.chg_boost_n.get_value() == 0:
            _, percent = self._get_battery_voltage()
            draw.text(
                (0, 10), f"Power    ON BATTERY ({percent}%)", font=self.font15, fill=0
            )
        else:
            draw.text((0, 10), "Power     CHARGED", font=self.font15, fill=0)

        # Wait rectangle
        self._draw_wait_rectangle(wait, draw)

        return image

    def _generate_setup_view(self, wait: bool) -> Image:
        """Generate the status view as an image

        Args:
            wait (bool): Indicates if wait message is printed

        Returns:
            Image: The status image
        """
        image = Image.new("1", (self.epd.height, self.epd.width), 255)
        draw = ImageDraw.Draw(image)

        try:
            def_gw_device = netifaces.gateways()["default"][netifaces.AF_INET][1]
            ip_addr = ni.ifaddresses(def_gw_device)[AF_INET][0]["addr"]
        except:  # noqa: E722
            ip_addr = "10.50.0.1"
        url = f"{ip_addr}"

        if os.system("systemctl is-active --quiet mapio-webserver-back") == 0:  # nosec
            draw.text((130, 0), f"{url}", font=self.font12, fill=0)
            draw.text((0, 100), "Webserver is running", font=self.font12, fill=0)
            draw.text((0, 110), "Press MID to disable server", font=self.font12, fill=0)

            # Check if current connexion is ok
            if not self._send_ping_command():
                self._enable_access_point()
                draw.text((0, 0), "WIFI AP ON", font=self.font12, fill=0)
                text_layer = Image.new("1", (90, 30), 255)
                draw_rot = ImageDraw.Draw(text_layer)
                draw_rot.text((0, 0), "SSID:MAPIO", font=self.font12, fill=0)
                draw_rot.text(
                    (0, 15), f"PASS:{self.wifi_passwd}", font=self.font12, fill=0
                )
                rotated_text_layer = text_layer.rotate(90.0, expand=1)
                image.paste(rotated_text_layer, (85, 10))

                wifi_data = f"WIFI:S:MAPIO;T:WPA;P:{self.wifi_passwd};;"
                addr_code = qrcode.QRCode(
                    error_correction=qrcode.constants.ERROR_CORRECT_H, border=0
                )
                addr_code.add_data(wifi_data)
                qr_img = addr_code.make_image().resize((80, 80))
                image.paste(qr_img, (0, 15))
            else:
                draw.text((0, 0), "WIFI AP OFF", font=self.font12, fill=0)

            addr_code = qrcode.QRCode(
                error_correction=qrcode.constants.ERROR_CORRECT_H, border=0
            )
            addr_code.add_data(f"http://{url}")
            qr_img = addr_code.make_image().resize((80, 80))
            image.paste(qr_img, (150, 15))

            if self.mid_press:
                self.mid_press = False
                os.system("systemctl stop mapio-webserver-back")  # nosec
                os.system("systemctl stop nginx")  # nosec
                os.system("systemctl stop wpa_supplicant-ap")  # nosec

        else:
            draw.text((30, 10), "Webserver is not running", font=self.font12, fill=0)
            draw.text((30, 80), "Press MID to enable it", font=self.font12, fill=0)

            if self.mid_press:
                self.mid_press = False
                os.system("systemctl start mapio-webserver-back")  # nosec
                os.system("systemctl start nginx")  # nosec

        # Wait rectangle
        self._draw_wait_rectangle(wait, draw)

        return image

    def _draw_wait_rectangle(self, wait: bool, draw: ImageDraw) -> Image:
        """Draw wait rectangle on an image

        Args:
            wait (bool): Boolean to indicate if the rectangle is filled
            draw (ImageDraw): The image to modify

        Returns:
            Image: The modified image
        """
        draw.rectangle((192, 96, 247, 121), fill=255, outline="black")
        if wait:
            draw.text((196, 100), "Wait...", font=self.font12, fill=0)

    def _send_ping_command(self) -> bool:
        """Send a ping command to test internet connection

        Returns:
            bool: True if ping is successful, False otherwise
        """
        command = ["ping", "-c", "1", "-W", "1", "8.8.8.8"]
        if subprocess.call(command) == 0:  # nosec
            return True
        else:
            return False

    def _enable_access_point(self) -> None:
        """Enable the WIFI access point with dynamic password

        If the access point was already active, this function does
        nothing.
        """
        if os.system("systemctl is-active wpa_supplicant-ap") == 0:  # nosec
            self.logger.debug("Access point WIFI is already active")
        else:
            self.logger.info("Enable WIFI access point")
            # Generate a random wifi password
            self.wifi_passwd = "".join(
                random.choice(string.ascii_lowercase) for i in range(8)
            )
            sed_arg = f's/psk=.*/psk="{self.wifi_passwd}"/g'
            # Replace the password in current access point configuration
            command = [
                "sed",
                "-i",
                sed_arg,
                "/etc/wpa_supplicant/wpa_supplicant-ap.conf",
            ]
            subprocess.call(command)
            os.system("systemctl stop wpa_supplicant@wlan0")  # nosec
            os.system("systemctl restart wpa_supplicant-ap")  # nosec

    def _get_battery_voltage(self) -> Tuple[float, int]:
        # Get PMIC model
        model = os.popen("vcgencmd pmicrd 0 | awk '{print $3}'").read()  # nosec
        if model.strip() == "a0":
            # MAX LINEAR MXL7704
            # Read AIN0 value
            battery_volt = os.popen(  # nosec
                "vcgencmd pmicrd 1d | awk '{print $3}'"  # nosec
            ).read()  # nosec
            battery_volt_int = 2 * int(battery_volt, 16) / 100
        else:
            # DA9090 PMIC
            # Read AIN0 value
            battery_volt = os.popen(  # nosec
                "vcgencmd pmicrd 0x13 | awk '{print $3}'"  # nosec
            ).read()  # nosec
            battery_volt_int = 4 * int(battery_volt, 16) / 100

        percent = 0
        if battery_volt_int > 4:
            percent = 100
        elif battery_volt_int > 3.75:
            percent = 75
        elif battery_volt_int > 3.5:
            percent = 50
        elif battery_volt_int > 3.25:
            percent = 25

        return battery_volt_int, percent


# Create MAPIO control object
# This object is global to app module
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
    mapio_ctrl.logger.info("Start refresh leds task")

    while True:
        # LED1 management
        # Check if docker service is running
        if os.system("systemctl is-active --quiet docker.service") == 0:  # nosec
            mapio_ctrl.led_sys_green.on()
            mapio_ctrl.led_sys_red.off()
        else:
            mapio_ctrl.led_sys_green.on()
            mapio_ctrl.led_sys_red.on()

        # LED3 management
        if mapio_ctrl.chg_chg_n.get_value() == 0:
            mapio_ctrl.logger.debug("Charging")
            mapio_ctrl.led_chg_red.off()
            mapio_ctrl.led_chg_green.blink()
        elif mapio_ctrl.chg_boost_n.get_value() == 0:
            mapio_ctrl.logger.debug("On Battery")
            mapio_ctrl.led_chg_green.off()
            mapio_ctrl.led_chg_red.off()
            mapio_ctrl.led_chg_green.on()
            mapio_ctrl.led_chg_red.on()
        else:
            mapio_ctrl.logger.debug("Charged")
            mapio_ctrl.led_chg_green.off()
            mapio_ctrl.led_chg_green.on()

        time.sleep(1)


def _gpio_chip_handler(buttons: Any) -> None:
    """Handler for GPIO buttons interrupts

    Args:
        buttons (Any): List of GPIO that trigs the interrupt
    """
    while True:
        lines = buttons.event_wait(datetime.timedelta(seconds=10))
        if not lines.empty:
            for it in lines:
                event = it.event_read()
                mapio_ctrl.logger.debug(f"Event: {event}")
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
                    mapio_ctrl.need_refresh = True
                    mapio_ctrl.mid_press = True
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
