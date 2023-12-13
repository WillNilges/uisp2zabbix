from pyzabbix import ZabbixAPI
import os
import logging
import weakref
from enum import Enum

from pyzabbix.api import ZabbixAPIException

SNMP_AGENT = 20
TRAPPER = 2

TEMPLATE_GROUP = "Templates/UISP2Zabbix"
HOST_GROUP = "UISP2Zabbix"

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


class ZabbixClient:
    def __init__(self):
        zabbix_url = os.getenv("ZABBIX_URL")
        zabbix_uname = os.getenv("ZABBIX_UNAME")
        zabbix_pword = os.getenv("ZABBIX_PWORD")
        if zabbix_url is None or zabbix_uname is None or zabbix_pword is None:
            logging.error(f"Zabbix credentials not provided")
            raise ValueError("Zabbix credentials not provided.")
        logging.info("Logging into zabbix...")
        self.zapi = ZabbixAPI(zabbix_url)
        self.zapi.login(zabbix_uname, zabbix_pword)
        logging.info(f"Logged into zabbix @ {zabbix_url}")
        self._finalizer = weakref.finalize(self, self._cleanup_conn, self.zapi)

        # Set up template group and template
        #self.template_group_id = self.get_or_create_template_group()
        self.host_group_id = self.get_or_create_host_group()
        # FIXME: Just p2p for now, but how about in the future?
        self.template_name = f"Point to Point by UISP2Zabbix"
        self.template_id = self.get_or_create_template()
        self.host_cache = {}

    @staticmethod
    def _cleanup_conn(zapi):
        zapi.user.logout()

    # FIXME: Template stuff isn't relevant this very second
    # Searches for M2ZA template group. Creates it if it doesn't already exist
    def get_or_create_template_group(self):
        try:
            # Check if the template group already exists
            existing_groups = self.zapi.templategroup.get(
                filter={"name": TEMPLATE_GROUP}
            )

            if existing_groups:
                print(f"Template group '{TEMPLATE_GROUP}' already exists.")
                return existing_groups[0]["groupid"]

            # Create the template group if it doesn't exist
            created_group = self.zapi.templategroup.create(name=TEMPLATE_GROUP)
            print(
                f"Template group '{TEMPLATE_GROUP}' created with ID: {created_group['groupids'][0]}"
            )
            self.template_group_id = created_group["groupids"][0]
            return created_group["groupids"][0]
        except ZabbixAPIException as e:
            print(f"Error creating template group: {e}")
            return None

    # Returns template_id, creates if it doesn't already exist
    def get_or_create_template(self):
        try:
            template = self.zapi.template.get(filter={"name": self.template_name})
            if template:
                return template[0]["templateid"]
            else:
                try:
                    template = self.zapi.template.create(
                        {
                            "host": self.template_name,  # Host is the template name. Not confusing at all :)
                            "groups": [{"groupid": self.template_group_id}],
                        }
                    )
                    print(
                        f"Template '{self.template_name}' created with ID {template['templateids'][0]}"
                    )
                    return template["templateids"][0]
                except ZabbixAPIException as e:
                    print(f"Error creating template: {e}")
                    return None
        except ZabbixAPIException as e:
            print(f"Error getting template: {e}")
            return None

    # Creates an item in a template
    def get_or_create_item(self, name, key, info_type, unit):
        print(key)

        try:
            item = self.zapi.item.get(
                filter={"key_": key}, templateids=[self.template_id]
            )

            if item:
                item_info = item[0]
                print(
                    f"Item found: {item_info['name']} (Item ID: {item_info['itemid']}, Key: {item_info['key_']})"
                )
                return item_info["itemid"]
            else:
                print(f"Item with key '{key}' not found.")

                # Create trapper item
                item_params = {
                    "name": name,
                    "key_": key,
                    "type": TRAPPER,
                    "value_type": info_type,
                    "hostid": self.template_id,
                    "units": unit,
                }

                try:
                    item_id = self.zapi.item.create(params=item_params)["itemids"][0]
                    print(
                        f"Trapper item '{name}' created successfully with item ID {item_id}"
                    )
                except Exception as e:
                    print(f"Failed to create trapper item: {e}")

        except ZabbixAPIException as e:
            print(f"Error: {e}")
            return None

    def get_or_create_host(self, host_name):
        # TODO: Create a cache so we don't have to bother Zabbix so much
        if host_name in self.host_cache.keys():
            return self.host_cache[host_name]

        # Check if the host already exists
        existing_host = self.zapi.host.get(filter={"host": host_name})

        if existing_host:
            # Host already exists, return its ID
            host_id = existing_host[0]['hostid']
            print(f"Host '{host_name}' already exists with ID {host_id}")
        else:
            # Host doesn't exist, create it
            host_create_params = {
                "host": host_name,
                "name": host_name,
                "groups": [{"groupid": self.host_group_id}],
                "templates": [{"templateid": self.template_id}],
            }

            host_info = self.zapi.host.create(host_create_params)
            host_id = host_info['hostids'][0]
            print(f"Host '{host_name}' created with ID {host_id}")

        self.host_cache[host_name] = host_id
        return host_id

    def get_or_create_host_group(self):
        # Check if the host group already exists
        existing_group = self.zapi.hostgroup.get(filter={"name": HOST_GROUP})

        if existing_group:
            # Host group already exists, return its ID
            group_id = existing_group[0]['groupid']
            print(f"Host group '{HOST_GROUP}' already exists with ID {group_id}")
        else:
            # Host group doesn't exist, create it
            group_create_params = {"name": HOST_GROUP}
            group_info = self.zapi.hostgroup.create(group_create_params)
            group_id = group_info['groupids'][0]
            print(f"Host group '{HOST_GROUP}' created with ID {group_id}")

        self.host_group_id = group_id
        return group_id

