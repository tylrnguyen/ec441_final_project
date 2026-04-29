import asyncio
import pyshark
import json
import os
from collections import defaultdict
from datetime import datetime

# pyshark needs an event loop on py3.10+
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())


class BaseParser:
    WINDOW_SEC = 1.0

    def __init__(self, filepath: str, label: str = ""):
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"pcap not found: {filepath}")
        self.filepath = filepath
        self.label = label or os.path.basename(filepath)
        self.packets_processed = 0
        self.start_epoch = None

        self._windows: list[dict] = []
        self._cur: dict = self._empty_win(0)

        self.proto_bytes = defaultdict(int)
        self.total_bytes = 0
        self.total_pkts = 0

    def run(self) -> dict:
        cap = pyshark.FileCapture(
            self.filepath,
            keep_packets=False,
            use_ek=False,
        )
        try:
            for pkt in cap:
                self._ingest(pkt)
        except Exception as e:
            print(f"  [warn] stopped early: {e}")
        finally:
            cap.close()

        if self._cur["pkt_count"] > 0:
            self._windows.append(self._cur)

        return self._build()

    def process_packet(self, pkt, rel: float, length: int) -> dict | None:
        return {}

    def _ingest(self, pkt):
        try:
            epoch = float(pkt.sniff_timestamp)
        except (AttributeError, ValueError):
            return

        if self.start_epoch is None:
            self.start_epoch = epoch

        rel = epoch - self.start_epoch
        length = int(pkt.length)
        proto = self._classify(pkt)

        extra = self.process_packet(pkt, rel, length)
        if extra is None:
            return

        self.total_bytes += length
        self.total_pkts += 1
        self.proto_bytes[proto] += length
        self.packets_processed += 1

        idx = int(rel // self.WINDOW_SEC)
        if idx > self._cur["win_idx"]:
            self._windows.append(self._cur)
            for gap in range(self._cur["win_idx"] + 1, idx):
                self._windows.append(self._empty_win(gap))
            self._cur = self._empty_win(idx)

        w = self._cur
        w["pkt_count"] += 1
        w["bytes"] += length
        w["protocols"][proto] = w["protocols"].get(proto, 0) + length

        for k, v in extra.items():
            if isinstance(v, (int, float)):
                w.setdefault(k, 0)
                w[k] += v
            elif isinstance(v, list):
                w.setdefault(k, [])
                w[k].extend(v)

    @staticmethod
    def _classify(pkt) -> str:
        layers = [l.layer_name.upper() for l in pkt.layers]
        for name in ("QUIC", "HTTP2", "HTTP", "TLS", "DNS", "STUN", "RTP", "RTCP", "DTLS"):
            if name in layers:
                return name
        if "UDP" in layers:
            return "UDP"
        if "TCP" in layers:
            return "TCP"
        if "ICMP" in layers:
            return "ICMP"
        return layers[-1] if layers else "OTHER"

    @staticmethod
    def _empty_win(idx: int) -> dict:
        return {
            "win_idx": idx,
            "time_sec": round(idx * BaseParser.WINDOW_SEC, 1),
            "pkt_count": 0,
            "bytes": 0,
            "protocols": {},
        }

    def _build(self) -> dict:
        dur = (
            self._windows[-1]["time_sec"] + self.WINDOW_SEC
            if self._windows
            else 0
        )
        for w in self._windows:
            w["throughput_kbps"] = round(
                (w["bytes"] * 8) / (self.WINDOW_SEC * 1000), 2
            )
            # rename for dashboard compat
            w["packet_count"] = w.pop("pkt_count")
            w["window_index"] = w.pop("win_idx")

        return {
            "label": self.label,
            "file": os.path.basename(self.filepath),
            "packets_processed": self.packets_processed,
            "duration_sec": round(dur, 1),
            "total_bytes": self.total_bytes,
            "avg_throughput_kbps": (
                round((self.total_bytes * 8) / (dur * 1000), 2)
                if dur > 0
                else 0
            ),
            "protocol_distribution": dict(self.proto_bytes),
            "timeseries": self._windows,
        }
