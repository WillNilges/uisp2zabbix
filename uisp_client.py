import os
import requests
import json

class UISPClient():
    def __init__(self):
        self.headers = {'x-auth-token': os.getenv("UISP_AUTH_TOKEN")}
        self.dev_endpoint = os.getenv("UISP_DEV_ENDPOINT")
        self.stats_endpoint = os.getenv("UISP_STATS_ENDPOINT")

    def get_devices(self):
        response = requests.get(self.dev_endpoint, headers=self.headers, verify=False)

        devices = json.loads(response.content)

        if devices == []:
            raise ValueError('Problem downloading UISP devices.')

        return devices
