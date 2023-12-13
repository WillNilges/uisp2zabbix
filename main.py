import time
import json
from dotenv import load_dotenv
from uisp_client import UISPClient


def main():
    load_dotenv()
    uisp = UISPClient()
    print(json.dumps(uisp.get_data_links(), indent=2))

if __name__ == "__main__":
    main()
