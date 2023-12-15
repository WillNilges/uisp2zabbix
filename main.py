from argparse import ArgumentParser
import dataclasses
import logging
import os
import time
import json
from dotenv import load_dotenv
from point_to_point import DataLinkStatistics, DataLink, build_datalink_template
from uisp_client import UISPClient
from zabbix_client import NUMERIC_FLOAT, NUMERIC_UNSIGNED, TEXT, ZabbixClient
from zappix.sender import Sender
from zappix.protocol import SenderData

if not os.path.exists("./log"):
    os.mkdir("./log")

logging.basicConfig(encoding="utf-8", level=logging.INFO)
log = logging.getLogger("UISP2Zabbix")


def main():
    parser = ArgumentParser(
        description="A broker for forwarding UISP device statistics to Zabbix."
    )

    parser.add_argument(
        "--dump",
        action="store_true",
        help="Dump one frame of UISP data to stdout and exit",
    )

    parser.add_argument(
        "--update-template",
        action="store_true",
        help="Force updating the items within a template",
    )

    args = parser.parse_args()

    load_dotenv()
    uisp = UISPClient()

    if args.dump:
        print(json.dumps(uisp.get_data_links(filter=True), indent=2))
        return

    # For talking to the Zabbix API. Also creates Default Template Group and
    # Default Host Group
    zapi = ZabbixClient()

    # Set up template for DataLinks (if needed)
    datalink_template_id, created = zapi.get_or_create_template(DataLink)
    if created or args.update_template:
        build_datalink_template(zapi, datalink_template_id)

    # For pushing data to Zabbix (doing the actual broker-ing)
    z_endpoint = os.getenv("ZABBIX_ENDPOINT")
    if not z_endpoint:
        raise ValueError("Must provide Zabbix endpoint")
    z_sender = Sender(z_endpoint)

    while True:
        z_payload = []
        logging.info("Querying UISP for Data Link info...")
        for l in uisp.get_data_links(filter=True):
            try:
                p2p = DataLink(
                    l["ssid"].strip(),
                    DataLinkStatistics(**l["from"]["interface"]["statistics"]),
                    DataLinkStatistics(**l["to"]["interface"]["statistics"]),
                )

                # Create the host if it doesn't already exist
                zapi.get_or_create_host(p2p.ssid, datalink_template_id)

                for k, v in p2p.stats().items():
                    z_payload.append(SenderData(p2p.ssid, f"{DataLink.prefix}.{k}", v))
            except Exception as e:
                log.exception(f"Got exception processing UISP payload: {e}")

        # Send collected payloads to Zabbix
        log.info("Sending collected metrics to Zabbix...")
        attempts_left = 2
        while attempts_left > 0:
            try:
                z_sender.send_bulk(z_payload, with_timestamps=True)
                break
            except Exception as e:
                attempts_left -= 1
                logging.exception(e)
                logging.error("Sleeping for 3 seconds and trying again.")
                time.sleep(3)

        # Sleep until it's time to gather more data
        sleep_duration = os.getenv("SLEEP_DURATION", default=10)
        log.info(f"Sleeping for {sleep_duration}s...")
        time.sleep(int(sleep_duration))


if __name__ == "__main__":
    main()
