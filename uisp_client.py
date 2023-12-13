import os
import requests
import json


class UISPClient:
    def __init__(self):
        self.headers = {"x-auth-token": os.getenv("UISP_AUTH_TOKEN")}
        self.endpoint = os.getenv("UISP_ENDPOINT")

        if not self.endpoint or not self.headers:
            raise ValueError("Missing environment variables.")

    def get_devices(self):
        response = requests.get(
            f"{self.endpoint}/devices", headers=self.headers, verify=False
        )

        devices = json.loads(response.content)

        if devices == []:
            raise ValueError("Problem downloading UISP devices.")

        return devices

    def get_stats(self, device_id):
        # Available interval values : hour, fourhours, day, week, month, quarter, year, range

        endpoint = f"{self.endpoint}/devices/{device_id}/statistics"
        params = {
            # "start":int(time.time() * 1000),
            # "period":int(11*60*1000),
            "interval": "hour",
        }
        response = requests.get(
            endpoint, headers=self.headers, params=params, verify=False
        )
        history = json.loads(response.content)
        return history

    def get_data_links(self):
        response = requests.get(
            f"{self.endpoint}/data-links", headers=self.headers, verify=False
        )

        data_links = json.loads(response.content)

        if data_links == []:
            raise ValueError("Problem downloading UISP data_links.")

        return data_links
