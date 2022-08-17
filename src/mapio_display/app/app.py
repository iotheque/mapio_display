import datetime
from pathlib import Path

import netifaces as ni  # type: ignore
from netifaces import AF_INET  # type: ignore
from PIL import Image, ImageDraw, ImageFont  # type: ignore

from mapio_display.epd.epd import EPD


def print_current_time(image: Image) -> None:
    """Add current time format HH::MM on current image

    Args:
        image (Image): Current base image
    """
    image_editable = ImageDraw.Draw(image)
    font = ImageFont.truetype("/usr/share/fonts/ttf/LiberationMono-Bold.ttf", 40)
    clock = datetime.datetime.now().strftime("%H:%M")
    image_editable.text((124, 2), clock, 0, font=font)


def print_os_version(image: Image) -> None:
    """Add current time format HH::MM on current image

    Args:
        image (Image): Current base image
    """
    try:
        image_editable = ImageDraw.Draw(image)
        font = ImageFont.truetype("/usr/share/fonts/ttf/LiberationMono-Bold.ttf", 12)
        version = Path("/etc/os-version").read_text()
        os_version = f"MAPIO OS : {version}"
    except AssertionError:
        os_version = "MAPIO OS : None"
    image_editable.text((124, 90), os_version, 0, font=font)


def print_ip_address(image: Image) -> None:
    """Add current time format HH::MM on current image

    Args:
        image (Image): Current base image
    """
    try:
        image_editable = ImageDraw.Draw(image)
        font = ImageFont.truetype("/usr/share/fonts/ttf/LiberationMono-Bold.ttf", 12)
        ip_addr = ni.ifaddresses("eth0")[AF_INET][0]["addr"]
    except AssertionError:
        ip_addr = "NO IP"
    image_editable.text((124, 70), ip_addr, 0, font=font)


def base_image_with_logo(epd: EPD) -> Image:
    """Create a base image with the MAPIO logo

    Args:
        epd (EPD): Epaper object

    Returns:
        Image: The generated base image
    """
    img = Image.open(f"{Path(__file__).parent}/../images/mapio_logo_bw104x122.jpg")
    image = Image.new("1", (epd.height, epd.width), 255)  # 255: clear the frame
    image.paste(img, (2, 2))
    return image


def mapio_refresh_main_screen(epd: EPD) -> None:
    """Refresh the data on mapio main screen

    Args:
        epd (EPD): Epaper object
    """
    epd.init()
    image = base_image_with_logo(epd)
    print_current_time(image)
    print_os_version(image)
    print_ip_address(image)
    epd.display(epd.getbuffer(image))
    epd.enter_deep_sleep()
