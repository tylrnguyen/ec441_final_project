import sys
import pyshark
import os

PCAP_FILES = {
    "netflix": "../data/netflix.pcap",
    "meet": "../data/meet.pcap",
    "discord": "../data/discord.pcap"
}

if len(sys.argv) < 2:
    print("Usage: python analyze_protocols.py <netflix|meet|discord>")
    sys.exit(1)

app = sys.argv[1].lower()

if app not in PCAP_FILES:
    print(f"Unknown app: {app}")
    sys.exit(1)

PCAP = PCAP_FILES[app]

if not os.path.exists(PCAP):
    print(f"File not found: {PCAP}")
    sys.exit(1)

cap = pyshark.FileCapture(PCAP)

tcp = 0          # num of TCP packets
udp = 0          # num of UDP packets
total = 0       
protocols = {}   # dictionary to count each protocol type

for packet in cap:
    total += 1

    # highest layer protocol for this packet
    proto = packet.highest_layer
    protocols[proto] = protocols.get(proto, 0) + 1

    # count TCP and UDP packets separately
    if hasattr(packet, "tcp"):
        tcp += 1
    elif hasattr(packet, "udp"):
        udp += 1

print(f"{app.capitalize()} Protocol Summary:")
print(f"Total Packets: {total}")
print(f"TCP Packets: {tcp} ({tcp/total*100:.2f}%)")
print(f"UDP Packets: {udp} ({udp/total*100:.2f}%)")

print("\nTop Protocols:")
for proto, count in sorted(protocols.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"{proto}: {count} packets ({count/total*100:.2f}%)")