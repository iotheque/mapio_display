"""Main app to control MAPIO display."""

import datetime
import hashlib
import os
import random
import string
import subprocess  # nosec
import threading
import time
from collections import deque
from enum import Enum
from pathlib import Path
from typing import Any

import netifaces  # type: ignore
import netifaces as ni  # type: ignore
import psutil  # type: ignore
import qrcode
from gpiod import chip, line_request  # type: ignore
from loguru import logger
from netifaces import AF_INET  # type: ignore
from PIL import Image, ImageDraw, ImageFont  # type: ignore

from mapio_display.epd.epd import EPD
from mapio_display.leds.leds import LED

SCREEN_REFRESH_PERIOD_S = 60


class BatteryState(Enum):
    """Enum that represents battery states."""

    powered = "POWERED"
    on_battery = "ON_BATTERY"
    critical = "CRITICAL_BATTERY"


class MAPIO_CTRL:
    """Contains all display interfaces."""

    def __init__(self) -> None:
        """Initialize MAPIO control object."""
        # ePaper control
        self.epd = EPD()
        self.views_list = ["HOME", "STATUS", "SETUP", "SYSTEM"]
        # check if there is a custom image to print
        if Path.exists(Path("/usr/local/homeassistant/media/epaper.jpg")):
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

        # Access point
        self.wifi_passwd = ""  # nosec

    # ePaper methods
    def get_current_buffered_image(self) -> Any:
        """Get current image as buffered.

        Args:
            wait (bool, optional): Indicates if wait message is printed. Defaults to False.

        Returns:
            Any: The buffered image
        """
        if self.current_view == "HOME":
            logger.info("HOME VIEW")
            image = self._generate_home_view()
        elif self.current_view == "SYSTEM":
            image = self._generate_system_view()
        elif self.current_view == "STATUS":
            image = self._generate_status_view()
        elif self.current_view == "SETUP":
            image = self._generate_setup_view()
        elif self.current_view == "CUSTOM":
            image = self._generate_custom_view()

        return self.epd.getbuffer(image)  # type: ignore

    def _generate_custom_view(self) -> Image.Image:
        """Generate the custom view as an image.

        Returns:
            Image: The custom view
        """
        image = Image.new("1", (self.epd.height, self.epd.width), 255)  # 255: clear the fmapio_ctre
        if Path.exists(Path("/usr/local/homeassistant/media/epaper.jpg")):
            img = Image.open("/usr/local/homeassistant/media/epaper.jpg")
            logger.info("Returns custom image")
            image.paste(img, (0, 0))
            return image
        return image

    def _generate_home_view(self) -> Image.Image:
        """Generate the home view as an image.

        Returns:
            Image: The home image
        """
        # Add logo
        img = Image.open(f"{Path(__file__).parent}/../images/mapio_logo_bw104x122.jpg")
        image = Image.new("1", (self.epd.height, self.epd.width), 255)  # 255: clear the frame
        image.paste(img, (2, 2))

        # Add hour
        draw: Any = ImageDraw.Draw(image)
        clock = datetime.datetime.now().strftime("%H:%M")  # noqa
        draw.text((120, 2), clock, 0, font=self.font40)

        # Add version
        try:
            image_editable: Any = ImageDraw.Draw(image)
            os_version = os.popen(
                "cat /etc/os-release | grep PRETTY_NAME | awk '{print $4}'"  # noqa
            ).read()
        except:  # noqa: E722
            os_version = "None"
        image_editable.text((120, 90), "MAPIO OS: ", 0, font=self.font12)  # type: ignore
        image_editable.text((120, 105), os_version, 0, font=self.font12)  # type: ignore

        # Add IP address
        try:
            image_editable = ImageDraw.Draw(image)
            def_gw_device = netifaces.gateways()["default"][netifaces.AF_INET][1]  # type: ignore
            ip_addr = ni.ifaddresses(def_gw_device)[AF_INET][0]["addr"]  # type: ignore
        except:  # noqa: E722
            ip_addr = "NO IP"
        image_editable.text((120, 70), ip_addr, 0, font=self.font12)  # type: ignore

        return image

    def _generate_system_view(self) -> Image.Image:
        """Generate the system view as an image.

        Returns:
            Image: The system image
        """
        image = Image.new("1", (self.epd.height, self.epd.width), 255)
        draw: Any = ImageDraw.Draw(image)
        draw.text((0, 0), "System ", font=self.font28, fill=0)

        draw.text((0, 30), f"•CPU: {psutil.cpu_percent()}%", font=self.font15, fill=0)
        draw.text(
            (115, 30),
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
        uptime = os.popen("uptime | awk -F ',' '{print $1}' | cut -c14-").read()  # noqa
        draw.text((115, 50), f"•Uptime: {uptime}", font=self.font15, fill=0)

        battery_volt, _ = self._get_battery_voltage()
        draw.text((0, 70), f"•Battery: {battery_volt}V", font=self.font15, fill=0)

        draw.text(
            (0, 90),
            f"•Temperature: {round(psutil.sensors_temperatures()['cpu_thermal'][0].current)}°C",
            font=self.font15,
            fill=0,
        )

        return image

    def _generate_status_view(self) -> Image.Image:
        """Generate the status view as an image.

        Returns:
            Image: The status image
        """
        image = Image.new("1", (self.epd.height, self.epd.width), 255)
        draw: Any = ImageDraw.Draw(image)
        draw.line([(0, 40), (255, 40)])
        draw.line([(0, 80), (255, 80)])
        if os.system("systemctl is-active --quiet docker.service") == 0:  # noqa
            draw.text((0, 90), "Docker    RUNNING", font=self.font15, fill=0)
        else:
            draw.text((0, 90), "Docker    STOPPED", font=self.font15, fill=0)

        if self._send_ping_command():
            draw.text((0, 50), "Internet  CONNECTED", font=self.font15, fill=0)
        else:
            draw.text((0, 50), "Internet  NOT CONNECTED", font=self.font15, fill=0)

        _, percent = self._get_battery_voltage()
        if self.get_battery_state() == BatteryState.powered:
            draw.text((0, 10), f"POWERED level: {percent}%", font=self.font15, fill=0)
        elif self.get_battery_state() == BatteryState.on_battery:
            draw.text((0, 10), f"ON BATTERY level: {percent}%", font=self.font15, fill=0)
        else:
            draw.text((0, 10), f"CRITICAL BATTERY level: {percent}%", font=self.font15, fill=0)

        return image

    def _generate_setup_view(self) -> Image.Image:
        """Generate the status view as an image.

        Returns:
            Image: The status image
        """
        image = Image.new("1", (self.epd.height, self.epd.width), 255)
        draw: Any = ImageDraw.Draw(image)

        try:
            def_gw_device = netifaces.gateways()["default"][netifaces.AF_INET][1]  # type: ignore
            ip_addr = ni.ifaddresses(def_gw_device)[AF_INET][0]["addr"]  # type: ignore
        except:  # noqa: E722
            ip_addr = "10.50.0.1"
        url = f"{ip_addr}"

        if os.system("systemctl is-active --quiet mapio-webserver-back") == 0:  # noqa
            draw.text((130, 0), f"{url}", font=self.font12, fill=0)
            draw.text((0, 100), "Webserver is running", font=self.font12, fill=0)
            draw.text((0, 110), "Press MID to disable server", font=self.font12, fill=0)

            # Check if current connexion is ok
            if not self._send_ping_command():
                self._enable_access_point()
                draw.text((0, 0), "WIFI AP ON", font=self.font12, fill=0)
                text_layer = Image.new("1", (90, 30), 255)
                draw_rot: Any = ImageDraw.Draw(text_layer)
                draw_rot.text((0, 0), "SSID:MAPIO", font=self.font12, fill=0)
                draw_rot.text((0, 15), f"PASS:{self.wifi_passwd}", font=self.font12, fill=0)
                rotated_text_layer = text_layer.rotate(90.0, expand=True)
                image.paste(rotated_text_layer, (85, 10))

                wifi_data = f"WIFI:S:MAPIO;T:WPA;P:{self.wifi_passwd};;"
                addr_code: Any = qrcode.QRCode(  # type: ignore
                    error_correction=qrcode.constants.ERROR_CORRECT_H, border=0  # type: ignore
                )
                addr_code.add_data(wifi_data)
                qr_img = addr_code.make_image().resize((80, 80))
                image.paste(qr_img, (0, 15))
            else:
                draw.text((0, 0), "WIFI AP OFF", font=self.font12, fill=0)

            addr_code = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, border=0)  # type: ignore
            addr_code.add_data(f"http://{url}")  # type: ignore
            qr_img: Any = addr_code.make_image().resize((80, 80))  # type: ignore
            image.paste(qr_img, (150, 15))

            if self.mid_press:
                self.mid_press = False
                os.system("systemctl stop mapio-webserver-back")  # noqa
                os.system("systemctl stop nginx")  # noqa
                os.system("systemctl stop wpa_supplicant-ap")  # noqa
                #  Update the image
                image = Image.new("1", (self.epd.height, self.epd.width), 255)
                draw: Any = ImageDraw.Draw(image)
                draw.text((30, 10), "Webserver is not running", font=self.font12, fill=0)
                draw.text((30, 80), "Press MID to enable it", font=self.font12, fill=0)

        else:
            draw.text((30, 10), "Webserver is not running", font=self.font12, fill=0)
            draw.text((30, 80), "Press MID to enable it", font=self.font12, fill=0)

            if self.mid_press:
                self.mid_press = False
                os.system("systemctl start mapio-webserver-back")  # noqa
                os.system("systemctl start nginx")  # noqa
                image = Image.new("1", (self.epd.height, self.epd.width), 255)
                draw: Any = ImageDraw.Draw(image)
                draw.text((30, 10), "Webserver is starting", font=self.font12, fill=0)
                draw.text((30, 80), "Please wait ...", font=self.font12, fill=0)
                mapio_ctrl.need_refresh = True

        return image

    def _send_ping_command(self) -> bool:
        """Send a ping command to test internet connection.

        Returns:
            bool: True if ping is successful, False otherwise
        """
        command = ["ping", "-c", "1", "-W", "1", "8.8.8.8"]
        if subprocess.call(command) == 0:  # noqa
            return True

        return False

    def _enable_access_point(self) -> None:
        """Enable the WIFI access point with dynamic password.

        If the access point was already active, this function does
        nothing.
        """
        if os.system("systemctl is-active wpa_supplicant-ap") == 0:  # noqa
            logger.debug("Access point WIFI is already active")
        else:
            logger.info("Enable WIFI access point")
            # Generate a random wifi password
            self.wifi_passwd = "".join(
                random.choice(string.ascii_lowercase) for _ in range(8)  # noqa
            )
            sed_arg = f's/psk=.*/psk="{self.wifi_passwd}"/g'
            # Replace the password in current access point configuration
            command = [
                "sed",
                "-i",
                sed_arg,
                "/etc/wpa_supplicant/wpa_supplicant-ap.conf",
            ]
            subprocess.call(command)  # noqa
            os.system("systemctl stop wpa_supplicant@wlan0")  # noqa
            os.system("systemctl restart wpa_supplicant-ap")  # noqa

    def _get_battery_voltage(self) -> tuple[float, int]:
        # Get PMIC model
        model = os.popen("vcgencmd pmicrd 0 | awk '{print $3}'").read()  # noqa
        if model.strip() == "a0":
            # MAX LINEAR MXL7704
            # Read AIN0 value
            battery_volt = os.popen("vcgencmd pmicrd 1d | awk '{print $3}'").read()  # noqa
            battery_volt_float = 2 * int(battery_volt, 16) / 100
        else:
            # DA9090 PMIC
            # Read AIN0 value
            battery_volt = os.popen("vcgencmd pmicrd 0x13 | awk '{print $3}'").read()  # noqa
            battery_volt_float = 4 * int(battery_volt, 16) / 100

        percent = 0
        if battery_volt_float > 4:
            percent = 100
        elif battery_volt_float > 3.75:
            percent = 75
        elif battery_volt_float > 3.5:
            percent = 50
        elif battery_volt_float > 3.25:
            percent = 25

        return battery_volt_float, percent

    def get_battery_state(self) -> BatteryState:
        """Return the current battery state."""
        state: BatteryState
        chg_boost_n = os.popen("gpioget --numeric -c 2 10").read().strip()  # noqa

        if chg_boost_n == "0":
            state = BatteryState.on_battery
        else:
            _, percent = self._get_battery_voltage()
            if percent <= 25:
                state = BatteryState.critical
            else:
                state = BatteryState.powered

        return state


# Create MAPIO control object
# This object is global to app module
mapio_ctrl = MAPIO_CTRL()


def refresh_screen_task() -> None:
    """Task that refresh the epaper screen."""
    next_refresh_time = round(time.time())
    logger.info("Start refresh screen task")
    prev_hash = 0

    while True:
        if (next_refresh_time + SCREEN_REFRESH_PERIOD_S < round(time.time())) or (
            mapio_ctrl.need_refresh is True
        ):
            mapio_ctrl.epd.init()
            mapio_ctrl.epd.is_busy = True
            next_refresh_time = round(time.time())
            mapio_ctrl.need_refresh = False
            # Update view for next refresh
            mapio_ctrl.current_view = mapio_ctrl.views_pool[0]
            image_array = mapio_ctrl.get_current_buffered_image()
            hash_function = hashlib.sha256()
            hash_function.update(image_array)
            new_hash = hash_function.hexdigest()
            logger.info(f"Image hash is {new_hash}")
            if new_hash != prev_hash:
                logger.info("Refresh the screen")
                mapio_ctrl.led_sys_green.blink(True)
                prev_hash = new_hash
                if mapio_ctrl.epd.display(image_array) is False:
                    mapio_ctrl.need_refresh = True
                    prev_hash = 0
            else:
                mapio_ctrl.epd.is_busy = False
                logger.info("No need to refresh")

        time.sleep(0.5)


def refresh_leds_task() -> None:
    """Task that refresh the leds."""
    logger.info("Start refresh leds task")

    while True:
        # LED1 management
        # Check if docker service is running
        if mapio_ctrl.epd.is_busy:
            pass
        elif os.system("systemctl is-active --quiet docker.service") == 0:  # noqa
            mapio_ctrl.led_sys_green.blink(False)
            mapio_ctrl.led_sys_green.on()
            mapio_ctrl.led_sys_red.off()
        else:
            mapio_ctrl.led_sys_green.blink(False)
            mapio_ctrl.led_sys_green.on()
            mapio_ctrl.led_sys_red.on()

        # LED3 management
        if mapio_ctrl.get_battery_state() == BatteryState.powered:
            logger.debug("Powered")
            mapio_ctrl.led_chg_red.off()
            mapio_ctrl.led_chg_green.on()
        elif mapio_ctrl.get_battery_state() == BatteryState.on_battery:
            logger.debug("On Battery")
            mapio_ctrl.led_chg_green.off()
            mapio_ctrl.led_chg_red.off()
            mapio_ctrl.led_chg_green.on()
            mapio_ctrl.led_chg_red.on()
        elif mapio_ctrl.get_battery_state() == BatteryState.critical:
            logger.debug("Crititcal Battery")
            mapio_ctrl.led_chg_red.on()
            mapio_ctrl.led_chg_green.off()
        time.sleep(1)


def _gpio_chip_handler(buttons: Any) -> None:
    """Handler for GPIO buttons interrupts.

    Args:
        buttons (Any): List of GPIO that trigs the interrupt
    """
    last_event_time = time.time()
    while True:
        lines = buttons.event_wait(datetime.timedelta(seconds=10))
        if not lines.empty:
            for it in lines:
                event = it.event_read()
                current_time = time.time()
                if current_time - last_event_time > 3:
                    last_event_time = current_time
                    logger.debug(f"Event: {event}")
                    if mapio_ctrl.epd.is_busy:
                        logger.info("ePaper is busy, ignore button event")
                    elif it.consumer == "UP":
                        mapio_ctrl.need_refresh = True
                        mapio_ctrl.views_pool.rotate(-1)
                        mapio_ctrl.led_sys_green.blink(True)
                        logger.info(f"next view is: {mapio_ctrl.views_pool[0]}")
                    elif it.consumer == "DOWN":
                        mapio_ctrl.need_refresh = True
                        mapio_ctrl.views_pool.rotate(1)
                        mapio_ctrl.led_sys_green.blink(True)
                        logger.info(f"next view is: {mapio_ctrl.views_pool[0]}")
                    elif it.consumer == "MID":
                        logger.info("MID has been pushed")
                        long_pressed = True
                        for _ in range(30):
                            if it.get_value() != 0:
                                long_pressed = False
                                break
                            time.sleep(0.1)
                        if long_pressed:
                            logger.info("Long pressed detected, ask for reboot")
                            mapio_ctrl.led_sys_green.off()
                            mapio_ctrl.led_sys_red.on()
                            os.system("reboot")  # noqa

                        mapio_ctrl.need_refresh = True
                        mapio_ctrl.mid_press = True
                        mapio_ctrl.led_sys_green.blink(True)
                    else:
                        logger.error("Unknown button")
                else:
                    logger.info("Debounce : ignore button event")
        time.sleep(1)


def gpio_mon_create_task() -> None:
    """Task that manages the GPIO buttons."""
    logger.info("Create GPIOs task")
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
    chip1 = chip(2)
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
