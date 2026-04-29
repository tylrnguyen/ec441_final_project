from .base_parser import BaseParser


class TCPParser(BaseParser):
    def __init__(self, filepath: str, label: str = ""):
        super().__init__(filepath, label)
        self.retrans = 0
        self.dup_acks = 0
        self.fast_retrans = 0
        self.ooo = 0
        self.win_sizes: list[int] = []

    def process_packet(self, pkt, rel: float, length: int) -> dict | None:
        if not hasattr(pkt, "tcp"):
            return {}

        tcp = pkt.tcp
        extra = {}

        try:
            win = int(tcp.window_size_value)
            self.win_sizes.append(win)
            extra["_wins"] = [win]
        except (AttributeError, ValueError):
            pass

        try:
            if hasattr(tcp, "analysis_retransmission"):
                self.retrans += 1
                extra["retransmissions"] = 1
        except Exception:
            pass

        try:
            if hasattr(tcp, "analysis_duplicate_ack"):
                self.dup_acks += 1
                extra["dup_acks"] = 1
        except Exception:
            pass

        try:
            if hasattr(tcp, "analysis_fast_retransmission"):
                self.fast_retrans += 1
                extra["fast_retransmits"] = 1
        except Exception:
            pass

        try:
            if hasattr(tcp, "analysis_out_of_order"):
                self.ooo += 1
                extra["out_of_order"] = 1
        except Exception:
            pass

        return extra

    def _build(self) -> dict:
        result = super()._build()

        result["tcp_summary"] = {
            "total_retransmissions": self.retrans,
            "total_dup_acks": self.dup_acks,
            "total_fast_retransmits": self.fast_retrans,
            "total_out_of_order": self.ooo,
            "retransmission_rate_pct": (
                round(self.retrans / self.packets_processed * 100, 3)
                if self.packets_processed
                else 0
            ),
            "avg_window_size": (
                round(sum(self.win_sizes) / len(self.win_sizes))
                if self.win_sizes
                else 0
            ),
        }

        for w in result["timeseries"]:
            w.setdefault("retransmissions", 0)
            w.setdefault("dup_acks", 0)
            wins = w.pop("_wins", [])
            w["avg_window_size"] = (
                round(sum(wins) / len(wins)) if wins else 0
            )

        return result
