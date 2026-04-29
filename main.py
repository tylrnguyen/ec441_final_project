#!/usr/bin/env python3
# usage: python main.py [--mock | path/to/file.pcapng]
# naming: {app}_{condition}.pcapng (e.g. meet_normal.pcapng)

import sys
import os
import json
import glob
import random
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TCPParser = None
UDPParser = None

def _load_parsers():
    global TCPParser, UDPParser
    if TCPParser is None:
        from parsers import TCPParser as _T, UDPParser as _U
        TCPParser = _T
        UDPParser = _U


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")

APP_PARSER = {"meet": "udp", "netflix": "tcp", "hulu": "tcp", "game": "udp", "discord": "udp"}
COND_LABELS = {"normal": "Normal", "latency": "100ms Added Latency", "loss": "2% Packet Loss"}
APP_LABELS = {"meet": "Google Meet", "netflix": "Netflix", "hulu": "Hulu", "game": "Online Game", "discord": "Discord"}


def parse_name(filename):
    base = os.path.splitext(os.path.basename(filename))[0]
    parts = base.split("_", 1)
    if len(parts) != 2:
        return None
    app, cond = parts
    if app in APP_PARSER and cond in COND_LABELS:
        return app, cond
    return None


def process_file(fpath):
    _load_parsers()
    parsed = parse_name(fpath)
    if parsed is None:
        print(f"  [info] unknown naming for {fpath}, using TCPParser")
        p = TCPParser(fpath, label=os.path.basename(fpath))
    else:
        app, cond = parsed
        label = f"{APP_LABELS.get(app, app)} — {COND_LABELS.get(cond, cond)}"
        Cls = TCPParser if APP_PARSER[app] == "tcp" else UDPParser
        p = Cls(fpath, label=label)

    print(f"  Parsing {os.path.basename(fpath)}...")
    res = p.run()
    print(f"  Done: {res['packets_processed']} packets, {res['duration_sec']}s")
    return res


def process_all():
    pcaps = sorted(
        glob.glob(os.path.join(DATA_DIR, "*.pcapng"))
        + glob.glob(os.path.join(DATA_DIR, "*.pcap"))
    )
    if not pcaps:
        print(f"No pcap files found in {DATA_DIR}/")
        print("Run with --mock to generate test data.")
        return

    results = {}
    for path in pcaps:
        parsed = parse_name(path)
        key = f"{parsed[0]}_{parsed[1]}" if parsed else os.path.splitext(os.path.basename(path))[0]
        results[key] = process_file(path)

    write_out(results)


def process_single(fpath):
    res = process_file(fpath)
    key = os.path.splitext(os.path.basename(fpath))[0]
    write_out({key: res})


def write_out(results):
    os.makedirs(OUT_DIR, exist_ok=True)

    dash = build_dash(results)
    outpath = os.path.join(OUT_DIR, "dashboard_data.json")
    with open(outpath, "w") as f:
        json.dump(dash, f, indent=2)
    print(f"\n✓ Dashboard JSON -> {outpath}")

    for key, res in results.items():
        p = os.path.join(OUT_DIR, f"{key}.json")
        with open(p, "w") as f:
            json.dump(res, f, indent=2)
        print(f"  + {p}")


def build_dash(results):
    apps = {}
    for key, data in results.items():
        parsed = parse_name(key + ".pcapng")
        if parsed:
            app, cond = parsed
        else:
            parts = key.split("_", 1)
            app = parts[0] if parts else key
            cond = parts[1] if len(parts) > 1 else "normal"

        if app not in apps:
            apps[app] = {}
        apps[app][cond] = data

    summary = []
    for ak, conds in apps.items():
        for ck, data in conds.items():
            row = {
                "app": APP_LABELS.get(ak, ak),
                "app_key": ak,
                "condition": COND_LABELS.get(ck, ck),
                "condition_key": ck,
                "avg_throughput_kbps": data.get("avg_throughput_kbps", 0),
                "total_packets": data.get("packets_processed", 0),
                "duration_sec": data.get("duration_sec", 0),
                "protocol_distribution": data.get("protocol_distribution", {}),
            }
            if "tcp_summary" in data:
                row["retransmission_rate_pct"] = data["tcp_summary"]["retransmission_rate_pct"]
                row["avg_window_size"] = data["tcp_summary"]["avg_window_size"]
            if "udp_summary" in data:
                row["avg_jitter_ms"] = data["udp_summary"]["avg_inter_arrival_ms"]
                row["udp_ratio_pct"] = data["udp_summary"]["udp_ratio_pct"]
            summary.append(row)

    return {"apps": apps, "summary": summary}


def gen_mock():
    print("Generating mock data...\n")
    results = {}

    cfgs = [
        ("meet_normal",   "meet",    "normal",  "udp", 2500, 0.1),
        ("meet_latency",  "meet",    "latency", "udp", 2100, 0.2),
        ("meet_loss",     "meet",    "loss",    "udp", 1800, 0.3),
        ("netflix_normal","netflix", "normal",  "tcp", 8000, 0.08),
        ("netflix_latency","netflix","latency", "tcp", 5500, 0.15),
        ("netflix_loss",  "netflix", "loss",    "tcp", 4200, 0.25),
        ("game_normal",   "game",    "normal",  "udp", 500,  0.05),
        ("game_latency",  "game",    "latency", "udp", 480,  0.12),
        ("game_loss",     "game",    "loss",    "udp", 420,  0.20),
    ]

    for key, app, cond, ptype, base_tp, noise in cfgs:
        label = f"{APP_LABELS[app]} — {COND_LABELS[cond]}"
        dur = 180
        nw = dur

        ts = []
        for i in range(nw):
            tp = base_tp * (1 + noise * math.sin(i * 0.1) + random.gauss(0, noise * 0.5))
            tp = max(0, tp)

            w = {
                "window_index": i,
                "time_sec": i * 1.0,
                "packet_count": int(tp / 8 + random.gauss(0, 10)),
                "bytes": int(tp * 1000 / 8),
                "throughput_kbps": round(tp, 2),
                "protocols": {},
            }

            if ptype == "tcp":
                rb = 0.001 if cond == "normal" else (0.01 if cond == "latency" else 0.03)
                w["retransmissions"] = max(0, int(random.gauss(w["packet_count"] * rb, 1)))
                w["dup_acks"] = max(0, int(random.gauss(w["retransmissions"] * 1.5, 1)))
                w["avg_window_size"] = int(random.gauss(
                    65535 if cond == "normal" else (32000 if cond == "latency" else 16000), 2000))
                w["protocols"] = {
                    "TCP": int(w["bytes"] * 0.6),
                    "TLS": int(w["bytes"] * 0.3),
                    "QUIC": int(w["bytes"] * 0.1),
                }
            else:
                jb = 2 if cond == "normal" else (15 if cond == "latency" else 25)
                w["avg_jitter_ms"] = round(abs(random.gauss(jb, jb * 0.3)), 2)
                if app == "meet":
                    w["protocols"] = {
                        "UDP": int(w["bytes"] * 0.4),
                        "STUN": int(w["bytes"] * 0.05),
                        "DTLS": int(w["bytes"] * 0.15),
                        "RTP": int(w["bytes"] * 0.35),
                        "TCP": int(w["bytes"] * 0.05),
                    }
                else:
                    w["protocols"] = {
                        "UDP": int(w["bytes"] * 0.85),
                        "TCP": int(w["bytes"] * 0.1),
                        "DNS": int(w["bytes"] * 0.05),
                    }

            ts.append(w)

        proto_dist = {}
        for w in ts:
            for p, b in w["protocols"].items():
                proto_dist[p] = proto_dist.get(p, 0) + b

        tot_bytes = sum(w["bytes"] for w in ts)
        tot_pkts = sum(w["packet_count"] for w in ts)

        res = {
            "label": label,
            "file": f"{key}.pcapng",
            "packets_processed": tot_pkts,
            "duration_sec": dur,
            "total_bytes": tot_bytes,
            "avg_throughput_kbps": round(tot_bytes * 8 / (dur * 1000), 2),
            "protocol_distribution": proto_dist,
            "timeseries": ts,
        }

        if ptype == "tcp":
            tot_r = sum(w.get("retransmissions", 0) for w in ts)
            res["tcp_summary"] = {
                "total_retransmissions": tot_r,
                "total_dup_acks": sum(w.get("dup_acks", 0) for w in ts),
                "total_fast_retransmits": int(tot_r * 0.3),
                "total_out_of_order": int(tot_r * 0.1),
                "retransmission_rate_pct": round(tot_r / max(tot_pkts, 1) * 100, 3),
                "avg_window_size": int(sum(w.get("avg_window_size", 0) for w in ts) / nw),
            }
        else:
            jitters = [w.get("avg_jitter_ms", 0) for w in ts if w.get("avg_jitter_ms", 0) > 0]
            res["udp_summary"] = {
                "total_udp_packets": int(tot_pkts * 0.85),
                "total_tcp_packets": int(tot_pkts * 0.15),
                "udp_ratio_pct": 85.0,
                "avg_inter_arrival_ms": round(sum(jitters) / max(len(jitters), 1), 3),
                "jitter_stdev_ms": round(max(jitters) - min(jitters), 3) if jitters else 0,
                "avg_packet_size": 800 if app == "meet" else (200 if app == "game" else 1200),
                "median_packet_size": 750 if app == "meet" else (180 if app == "game" else 1100),
            }

        results[key] = res

    write_out(results)
    print("\n✓ Mock data ready.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--mock":
            gen_mock()
        elif os.path.isfile(arg):
            process_single(arg)
        else:
            print(f"File not found: {arg}")
            sys.exit(1)
    else:
        process_all()
