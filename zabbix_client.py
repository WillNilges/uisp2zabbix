from pyzabbix import ZabbixAPI
import os
import logging
import weakref
from enum import Enum

from pyzabbix.api import ZabbixAPIException

SNMP_AGENT = 20
TRAPPER = 2

DEFAULT_TEMPLATE_GROUP = "Templates/UISP2Zabbix"
DEFAULT_HOST_GROUP = "UISP2Zabbix"

"""
Zabbix value_types
0 - numeric float;
1 - character;
2 - log;
3 - numeric unsigned;
4 - text.
"""
NUMERIC_FLOAT = 0
CHARACTER = 1
LOG = 2
NUMERIC_UNSIGNED = 3
TEXT = 4

log = logging.getLogger("UISP2Zabbix")


class ZabbixClient:
    def __init__(self):
        zabbix_url = os.getenv("ZABBIX_URL")
        zabbix_uname = os.getenv("ZABBIX_UNAME")
        zabbix_pword = os.getenv("ZABBIX_PWORD")
        if zabbix_url is None or zabbix_uname is None or zabbix_pword is None:
            log.exception(f"Zabbix credentials not provided")
            raise ValueError("Zabbix credentials not provided.")
        log.info("Logging into zabbix...")
        self.zapi = ZabbixAPI(zabbix_url)
        self.zapi.login(zabbix_uname, zabbix_pword)
        log.info(f"Logged into zabbix @ {zabbix_url}")
        self._finalizer = weakref.finalize(self, self._cleanup_conn, self.zapi)

        # Set up template group for templates from this app if needed
        self.default_template_group_id = self.get_or_create_template_group()

        # Set up host group for hosts created by this app if needed
        # By default, all hosts created will just be in the UISP2Zabbix
        # group
        self.default_host_group_id = self.get_or_create_host_group()

        # For caching hosts
        self.host_cache = {}
        self.template_cache = {}

    @staticmethod
    def _cleanup_conn(zapi):
        zapi.user.logout()

    # Queries the Zabbix API to check if a template group by the given name
    # exists, creates one if it doesn't, and returns the ID of that template group
    # Parameters: template_group_name (Name of Template Group) (Optional)
    # Returns: template_group_id (ID of Template Group)
    def get_or_create_template_group(self, template_group_name=DEFAULT_TEMPLATE_GROUP):
        try:
            # Check if the template group already exists
            existing_groups = self.zapi.templategroup.get(
                filter={"name": template_group_name}
            )

            if existing_groups:
                print(f"Template group '{template_group_name}' already exists.")
                return existing_groups[0]["groupid"]

            # Create the template group if it doesn't exist
            created_group = self.zapi.templategroup.create(name=template_group_name)
            print(
                f"Template group '{template_group_name}' created with ID: {created_group['groupids'][0]}"
            )
            return created_group["groupids"][0]
        except ZabbixAPIException as e:
            print(f"Error creating template group: {e}")
            return None

    # Queries the Zabbix API to check if a host group by the given name
    # exists, creates one if it doesn't, and returns the ID of that host group
    # Parameters: host_group_name (Name of Host Group) (Optional)
    # Returns: host_group_id (ID of Host Group)
    def get_or_create_host_group(self, host_group_name=DEFAULT_HOST_GROUP):
        try:
            # Check if the host group already exists
            existing_groups = self.zapi.hostgroup.get(filter={"name": host_group_name})

            if existing_groups:
                print(f"host group '{host_group_name}' already exists.")
                return existing_groups[0]["groupid"]

            # Create the host group if it doesn't exist
            created_group = self.zapi.hostgroup.create(name=host_group_name)
            print(
                f"host group '{host_group_name}' created with ID: {created_group['groupids'][0]}"
            )
            return created_group["groupids"][0]
        except ZabbixAPIException as e:
            print(f"Error creating host group: {e}")
            return None

    # Queries the Zabbix API to check if a template by the given name
    # exists, creates one if it doesn't, and returns the ID of that template
    # Parameters: template_name (Name of template)
    # Returns: template_id (ID of template)
    def get_or_create_template(self, data_class, template_group_id=None):
        if template_group_id is None:
            template_group_id = self.default_template_group_id
        template_name = f"{data_class.__name__} by UISPZabbix"

        # Check our cache for the template
        if template_name in self.template_cache.keys():
            template_id = self.template_cache[template_name]
            log.info(f"Found Template '{template_name}' with ID {template_id} in cache")
            return (template_id, False)

        try:
            # Check if the template exists
            template = self.zapi.template.get(filter={"host": template_name})
            if template:
                log.info(
                    f"Found Template '{template_name}' with ID {template[0]['templateid']}"
                )
                return (template[0]["templateid"], False)

            # If not, create it
            template = self.zapi.template.create(
                {"host": template_name, "groups": [{"groupid": template_group_id}]}
            )
            print(
                f"Template '{template_name}' created with ID {template['templateids'][0]}"
            )
            return (template["templateids"][0], True)

        except ZabbixAPIException as e:
            print(f"Error getting template: {e}")
            return (None, False)

    # Queries the Zabbix API to check if a item by the given name
    # exists, creates one if it doesn't, and returns the ID of that item
    # Parameters: item_name (Name of item), key, info_type, unit
    # Returns: item_id (ID of item)
    def get_or_create_template_item(
        self, template_id, name, key, value_type, unit=None, update=False
    ):
        log.info(f"Creating {key}")

        if unit is None:
            unit = ""

        try:
            # Check if the item exists
            item = self.zapi.item.get(filter={"key_": key}, templateids=[template_id])

            if item:
                item_info = item[0]
                log.info(
                    f"Item found: {item_info['name']} (Item ID: {item_info['itemid']}, Key: {item_info['key_']})"
                )
                if update:
                    self.zapi.item.update(
                        itemid=item_info["itemid"],
                        name=name,
                        key_=key,
                        # hostid = template_id,
                        type=TRAPPER,
                        value_type=value_type,
                        units=unit,
                    )["itemids"][0]

                    log.info(
                        f"Item '{name}' updated successfully with item ID {item_info['itemid']}"
                    )

                return item_info["itemid"]

            # If not, create it
            log.info(f"Item with key '{key}' not found.")

            # Create trapper item
            item_id = self.zapi.item.create(
                name=name,
                key_=key,
                hostid=template_id,
                type=TRAPPER,
                value_type=value_type,
                units=unit,
            )["itemids"][0]

            log.info(f"Item '{key}' created successfully with item ID {item_id}")

            return item_id
        except ZabbixAPIException as e:
            log.exception(f"Error: {e}")
            return None

    def get_or_create_host(self, host_name, template_id, host_group_id=None):
        if host_group_id is None:
            host_group_id = self.default_host_group_id

        # Check our cache for the host
        if host_name in self.host_cache.keys():
            host_id = self.host_cache[host_name]
            log.info(f"Found Host '{host_name}' with ID {host_id} in cache")
            return host_id

        # Check if the host already exists
        existing_host = self.zapi.host.get(filter={"host": host_name})

        if existing_host:
            # Host already exists, return its ID
            host_id = existing_host[0]["hostid"]
            log.info(f"Host '{host_name}' already exists with ID {host_id}")
        else:
            # Host doesn't exist, create it
            host_create_params = {
                "host": host_name,
                "name": host_name,
                "groups": [{"groupid": host_group_id}],
                "templates": [{"templateid": template_id}],
            }

            host_info = self.zapi.host.create(host_create_params)
            host_id = host_info["hostids"][0]
            log.info(f"Host '{host_name}' created with ID {host_id}")

        self.host_cache[host_name] = host_id
        return host_id
