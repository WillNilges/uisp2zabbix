from dataclasses import dataclass

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

    def stats(self):
        stats = {}

        for k, v in self.from_stats.__dict__.items():
            stats[f"from_{k}"] = v

        for k, v in self.to_stats.__dict__.items():
            stats[f"to_{k}"] = v

        return stats

