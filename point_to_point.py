from dataclasses import dataclass


class PointToPoint:
    ssid: str
    from_tx_rate: int
    from_rx_rate: int
    from_signal_local: int
    from_signal_remote: int
    to_tx_rate: int
    to_rx_rate: int
    to_signal_local: int
    to_signal_remote: int

    def __init__(self, ssid, from_stats, to_stats):
        self.ssid = ssid
        self.from_tx_rate = from_stats.txRate
        self.from_rx_rate = from_stats.rxRate
        self.from_signal_local = from_stats.signalLocal
        self.from_signal_remote = from_stats.signalRemote
        self.to_tx_rate = to_stats.txRate
        self.to_rx_rate = to_stats.rxRate
        self.to_signal_local = to_stats.signalLocal
        self.to_signal_remote = to_stats.signalRemote


@dataclass
class Statistics:
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
