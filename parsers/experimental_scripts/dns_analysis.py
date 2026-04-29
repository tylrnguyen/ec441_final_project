import sys
import pyshark
import os

PCAP_FILES = {
    "netflix": "../data/netflix.pcap",
    "meet": "../data/meet.pcap",
    "discord": "../data/discord.pcap"
}

if len(sys.argv) < 2:
    print("Usage: python dns_analysis.py <netflix|meet|discord>")
    sys.exit(1)

app = sys.argv[1].lower()

if app not in PCAP_FILES:
    print(f"Unknown app: {app}")
    sys.exit(1)

PCAP = PCAP_FILES[app]

if not os.path.exists(PCAP):
    print(f"File not found: {PCAP}")
    sys.exit(1)

# filter only for DNS packets
cap = pyshark.FileCapture(PCAP, display_filter="dns")

# set to store unique domain names for no duplicates
queries = set()

for packet in cap:
    try:
        # extra query name is exists 
        if hasattr(packet.dns, "qry_name"):
            queries.add(packet.dns.qry_name)
    except AttributeError:
        pass

#results 
print(f"DNS Queries in {app.capitalize()} Capture")

if not queries:
    print("No DNS queries found.")
    print("Likely captured after DNS resolution phase.")
else:
    for q in sorted(queries):
        print(q)