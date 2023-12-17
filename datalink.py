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


class DataLink(HostProto):
    name: str
    tags: dict
    from_stats: DataLinkStatistics
    to_stats: DataLinkStatistics
    prefix = "uisp2zabbix.p2p"

    def __init__(self, name, from_site, to_site, from_stats, to_stats):
        self.name = name
        self.tags = {"from": from_site, "to": to_site}
        self.from_stats = from_stats
        self.to_stats = to_stats

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
