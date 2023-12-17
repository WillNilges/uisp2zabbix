from dataclasses import dataclass
import dataclasses
from typing import Protocol

from zabbix_client import NUMERIC_FLOAT, TEXT, TemplateItem


class HostProto(Protocol):
    name: str
    tags: dict
    prefix: str

    # Parsing stats
    def stats(self) -> dict:
        ...

    # For creating a template automatically in Zabbix
    # TODO: Figure out better way to define templates
    @staticmethod
    def build_template():
        ...


# TODO: One day, I bet that I'll realize that all of these classes can
# be used for any UISP object. I think that Stats, plus Identification,
# plus a couple other things will equal a Site, and then a DataLink
# can be two Sites.

# It is already becoming the case that the names of these classes
# aren't really super accurate. a Site is just a way to refer to half of a
# DataLink, among other things.

# I'd like to actually try adding some other thing before committing to it, though.
# Becuase there's a pretty high chance we might not care. Maybe if we add routers.


@dataclass
class DataLinkStatistics:
    rxRate: int
    txRate: int
    downlinkCapacity: int
    uplinkCapacity: int
    downlinkUtilization: float
    uplinkUtilization: float
    signalLocal: int
    signalRemote: int
    signalChain0: int
    signalChain1: int
    signalRemoteChain0: int
    signalRemoteChain1: int
    linkScore: float
    score: int
    scoreMax: int
    airTimeScore: int
    linkScoreHint: str
    theoreticalDownlinkCapacity: int
    theoreticalUplinkCapacity: int


@dataclass
class DataLinkDeviceID:
    id: str
    name: str
    displayName: str
    model: str
    type: str
    category: str
    role: str
    authorized: bool


class DataLink(HostProto):
    name: str
    tags: dict
    from_stats: DataLinkStatistics
    to_stats: DataLinkStatistics
    prefix = "uisp2zabbix.p2p"

    # Manually define a Link
    def __init__(self, name, from_site, to_site, from_stats, to_stats):
        self.name = name
        self.tags = {"from": from_site, "to": to_site}
        self.from_stats = from_stats
        self.to_stats = to_stats

    # Or just use the JSON blob :)
    def __init__(self, link_json):
        self.name = link_json["ssid"].strip()
        self.tags = {
            "from": link_json["from"]["site"]["identification"]["name"],
            "to": link_json["to"]["site"]["identification"]["name"],
            "from_dev": link_json["from"]["device"]["identification"]["model"],
            "to_dev": link_json["to"]["device"]["identification"]["model"],
        }
        self.from_stats = DataLinkStatistics(
            **link_json["from"]["interface"]["statistics"]
        )
        self.to_stats = DataLinkStatistics(**link_json["to"]["interface"]["statistics"])

    def stats(self):
        stats = {}

        for k, v in self.from_stats.__dict__.items():
            stats[f"from_{k}"] = v

        for k, v in self.to_stats.__dict__.items():
            stats[f"to_{k}"] = v

        return stats

    @staticmethod
    def build_template():
        # Set up the items in the new template
        items = []
        for field in dataclasses.fields(DataLinkStatistics):
            if field.type == float or field.type == int:
                t = NUMERIC_FLOAT
                if "signal" in field.name:
                    u = "dB"
                elif "Rate" in field.name or "Capacity" in field.name:
                    u = "bps"  # TODO: Is this bps or Kbps?
                else:
                    u = ""
            else:
                t = TEXT
                u = ""

            for direction in ["from", "to"]:
                items.append(
                    TemplateItem(
                        f"{direction}_{field.name}",
                        f"{DataLink.prefix}.{direction}_{field.name}",
                        t,
                        u,
                    )
                )
        return items
