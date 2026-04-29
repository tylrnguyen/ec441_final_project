import statistics
from .base_parser import BaseParser


class UDPParser(BaseParser):
    def __init__(self, filepath: str, label: str = ""):
        super().__init__(filepath, label)
        self._last: dict[str, float] = {}
        self._jitter: list[float] = []
        self._sizes: list[int] = []
        self.udp_count = 0
        self.tcp_count = 0

    def process_packet(self, pkt, rel: float, length: int) -> dict | None:
        self._sizes.append(length)

        if hasattr(pkt, "udp"):
            self.udp_count += 1
        elif hasattr(pkt, "tcp"):
            self.tcp_count += 1

        if not hasattr(pkt, "udp"):
            return {}

        extra = {}

        try:
            epoch = float(pkt.sniff_timestamp)
            src = str(pkt.ip.src) if hasattr(pkt, "ip") else "?"
            dst = str(pkt.ip.dst) if hasattr(pkt, "ip") else "?"
            sport = str(pkt.udp.srcport)
            dport = str(pkt.udp.dstport)
            fk = f"{src}:{sport}->{dst}:{dport}"

            if fk in self._last:
                iat_ms = (epoch - self._last[fk]) * 1000
                self._jitter.append(iat_ms)
                extra["_jsamp"] = [iat_ms]

            self._last[fk] = epoch
        except (AttributeError, ValueError):
            pass

        return extra

    def _build(self) -> dict:
        result = super()._build()

        avg_j = (
            round(statistics.mean(self._jitter), 3)
            if self._jitter
            else 0
        )
        std_j = (
            round(statistics.stdev(self._jitter), 3)
            if len(self._jitter) > 1
            else 0
        )

        result["udp_summary"] = {
            "total_udp_packets": self.udp_count,
            "total_tcp_packets": self.tcp_count,
            "udp_ratio_pct": (
                round(self.udp_count / self.packets_processed * 100, 1)
                if self.packets_processed
                else 0
            ),
            "avg_inter_arrival_ms": avg_j,
            "jitter_stdev_ms": std_j,
            "avg_packet_size": (
                round(statistics.mean(self._sizes))
                if self._sizes
                else 0
            ),
            "median_packet_size": (
                round(statistics.median(self._sizes))
                if self._sizes
                else 0
            ),
        }

        for w in result["timeseries"]:
            samps = w.pop("_jsamp", [])
            w["avg_jitter_ms"] = (
                round(statistics.mean(samps), 2) if samps else 0
            )

        return result
