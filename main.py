import json
from pathlib import Path

from parsers.tcp_parser import TCPParser
from parsers.udp_parser import UDPParser

DATASETS = [
    {
        "app": "Netflix",
        "condition": "baseline",
        "pcap_file": "data/netflix.pcapng"
    },
    {
        "app": "Google Meet",
        "condition": "baseline",
        "pcap_file": "data/meet.pcapng"
    },
    {
        "app": "Discord",
        "condition": "baseline",
        "pcap_file": "data/discord.pcapng"
    }
]


def analyze_dataset(dataset):
    pcap_path = dataset["pcap_file"]

    return {
        "app": dataset["app"],
        "condition": dataset["condition"],
        "pcap": pcap_path,
        "tcp": TCPParser(pcap_path).parse(),
        "udp": UDPParser(pcap_path).parse()
    }


def main():
    results = []

    for dataset in DATASETS:
        print(f"Analyzing {dataset['app']} ({dataset['condition']})...")
        results.append(analyze_dataset(dataset))

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    with open(output_dir / "data.json", "w") as f:
        json.dump({"captures": results}, f, indent=2)

    print("Wrote outputs/data.json")


if __name__ == "__main__":
    main()