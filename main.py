import os
import time
import json
from dotenv import load_dotenv
from point_to_point import PointToPoint, Statistics
from uisp_client import UISPClient
from zabbix_client import ZabbixClient
from zappix.sender import Sender
from zappix.protocol import SenderData


def main():
    load_dotenv()
    uisp = UISPClient()
    #zapi = ZabbixClient()
    z_endpoint = os.getenv("ZABBIX_ENDPOINT")
    if not z_endpoint:
        raise ValueError("Must provide Zabbix endpoint")
    z_sender = Sender(z_endpoint)

    z_payload = []
    for l in uisp.get_data_links():

        # For now, this software is only interested in Point to Point links,
        # created by airMax

        devices = ("airFiber", "airMax", "wave", "wlan")
        wireless_modes = ("ap-ptp", "sta-ptp", "ap-ptmp-airmax-ac", "ap-ptmp-airmax-mixed")
        series = ("classic", "G60", "LTU")

        # Filter results
        #if l["type"] != "wireless":
        #    continue

#        if l["from"]["device"]["identification"]["type"] not in devices and l["to"]["device"]["identification"]["type"] not in devices:
#            continue

        if l["from"]["device"]["overview"]["wirelessMode"] not in wireless_modes or l["to"]["device"]["overview"]["wirelessMode"] not in wireless_modes:
            continue

        #print(l["ssid"])
        #print(json.dumps(l, indent=2))

        from_stats = Statistics(**l["from"]["interface"]["statistics"])
        to_stats = Statistics(**l["to"]["interface"]["statistics"])
        p2p = PointToPoint(l["ssid"], from_stats, to_stats)

        payload = json.loads(json.dumps(p2p.__dict__))
        for k, v in payload.items():
            z_payload.append(SenderData(l["ssid"], f"uisp2zabbix.p2p.{k}", v))
        break
        return
    z_sender.send_bulk(z_payload, with_timestamps=True)


if __name__ == "__main__":
    main()
