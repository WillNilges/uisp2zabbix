import time
import json
from dotenv import load_dotenv
from uisp_client import UISPClient


def main():
    load_dotenv()
    uisp = UISPClient()
    for l in uisp.get_data_links():

        # For now, this software is only interested in Point to Point links,
        # created by airMax

        devices = ("airFiber", "airMax", "wave", "wlan")
        wireless_modes = ("ap-ptp", "sta-ptp", "ap-ptmp-airmax-ac", "ap-ptmp-airmax-mixed")
        series = ("classic", "G60", "LTU")

        # Filter results
        if l["type"] != "wireless":
            continue

#        if l["from"]["device"]["identification"]["type"] not in devices and l["to"]["device"]["identification"]["type"] not in devices:
#            continue

        if l["from"]["device"]["overview"]["wirelessMode"] not in wireless_modes or l["to"]["device"]["overview"]["wirelessMode"] not in wireless_modes:
            continue

        print(l["ssid"])

if __name__ == "__main__":
    main()
