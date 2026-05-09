import time
import os
import psutil

from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont

serial = i2c(port=1, address=0x3C)
device = ssd1306(serial)

font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)

def get_cpu_temp():
    try:
        temp = os.popen("vcgencmd measure_temp").readline().strip()
        return temp.replace("temp=", "")
    except:
        return "N/A"

def get_ssd_temp():
    try:
        output = os.popen("sudo /usr/sbin/smartctl -A -d sat /dev/sda | grep Temperature_Celsius").read().strip()
        if output:
            parts = output.split()
            if len(parts) >= 10:
                return parts[9] + "C"
        return "N/A"
    except:
        return "N/A"

def get_disk_usage(path):
    try:
        return f"{psutil.disk_usage(path).percent}%"
    except:
        return "N/A"

while True:
    image = Image.new("1", (128, 64))
    draw = ImageDraw.Draw(image)

    cpu = psutil.cpu_percent(interval=0.2)
    ram = psutil.virtual_memory().percent
    cpu_temp = get_cpu_temp()
    ssd_temp = get_ssd_temp()
    disk_ssd = get_disk_usage("/mnt/ssd")

    draw.text((0, 0),  f"CPU T: {cpu_temp}", font=font, fill=255)
    draw.text((0, 12), f"SSD T: {ssd_temp}", font=font, fill=255)
    draw.text((0, 28), f"CPU: {cpu}%", font=font, fill=255)
    draw.text((0, 40), f"RAM: {ram}%", font=font, fill=255)
    draw.text((0, 52), f"SSD: {disk_ssd}", font=font, fill=255)

    device.display(image)
    time.sleep(1)
