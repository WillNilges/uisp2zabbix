import logging
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
    zapi = ZabbixClient()
    z_endpoint = os.getenv("ZABBIX_ENDPOINT")
    if not z_endpoint:
        raise ValueError("Must provide Zabbix endpoint")
    z_sender = Sender(z_endpoint)

    while True:
        z_payload = []
        for l in uisp.get_data_links():
            try:
                # TODO: For now, this software is only interested in Point to Point links
                wireless_modes = ("ap-ptp", "sta-ptp")
                if (
                    l["from"]["device"]["overview"]["wirelessMode"]
                    not in wireless_modes
                    or l["to"]["device"]["overview"]["wirelessMode"]
                    not in wireless_modes
                ):
                    continue

                # If the SSID doesn't exist, bail.
                if l["ssid"] is None:
                    continue

                # Trim whitespace
                host_name = l["ssid"].strip()

                from_stats = Statistics(**l["from"]["interface"]["statistics"])
                to_stats = Statistics(**l["to"]["interface"]["statistics"])
                p2p = PointToPoint(host_name, from_stats, to_stats)

                # Create the host if it doesn't already exist
                zapi.get_or_create_host(p2p.ssid)

                payload = json.loads(json.dumps(p2p.__dict__))
                for k, v in payload.items():
                    z_payload.append(SenderData(p2p.ssid, f"uisp2zabbix.p2p.{k}", v))
            except Exception as e:
                logging.exception(f"Got exception processing UISP payload: {e}")

        # Send collected payloads to Zabbix
        z_sender.send_bulk(z_payload, with_timestamps=True)

        # Sleep until it's time to gather more data
        sleep_duration = os.getenv("SLEEP_DURATION", default=10)
        logging.info(f"Sleeping for {sleep_duration}s...")
        time.sleep(int(sleep_duration))


if __name__ == "__main__":
    main()
