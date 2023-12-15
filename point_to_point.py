from dataclasses import dataclass
import dataclasses

from zabbix_client import NUMERIC_FLOAT, TEXT


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
class DataLink:
    ssid: str
    from_stats: DataLinkStatistics
    to_stats: DataLinkStatistics
    prefix = "uisp2zabbix.p2p"

    def stats(self):
        stats = {}

        for k, v in self.from_stats.__dict__.items():
            stats[f"from_{k}"] = v

        for k, v in self.to_stats.__dict__.items():
            stats[f"to_{k}"] = v

        return stats


def build_datalink_template(zapi, datalink_template_id):
    # Set up the items in the new template
    for field in dataclasses.fields(DataLinkStatistics):
        if field.type == float or field.type == int:
            t = NUMERIC_FLOAT
            if "signal" in field.name:
                u = "dB"
            elif "Rate" in field.name or "Capacity" in field.name:
                u = "bps"  # TODO: Is this bps or Kbps?
            else:
                u = None
        else:
            t = TEXT
            u = None

        for direction in ["from", "to"]:
            zapi.get_or_create_template_item(
                datalink_template_id,
                f"{direction}_{field.name}",
                f"{DataLink.prefix}.{direction}_{field.name}",
                t,
                u,
                update=True,
            )
