import sys
import pyshark
import os

PCAP_FILES = {
    "netflix": "../data/netflix.pcap",
    "meet": "../data/meet.pcap",
    "discord": "../data/discord.pcap"
}

if len(sys.argv) < 2:
    print("Usage: python packet_stats.py <netflix|meet|discord>")
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

# lists for storing packet sizes and timestamps
sizes = []       
timestamps = []  

# iterate through all packets and collect their sizes and timestamps
for packet in cap:
    sizes.append(int(packet.length))
    timestamps.append(float(packet.sniff_timestamp))

# how long the capture lasted
duration = max(timestamps) - min(timestamps)

print(f"{app.capitalize()} Packet Statistics:")
print(f"Packet count:       {len(sizes)}")
print(f"Capture duration:   {duration:.2f} seconds")
print(f"Average packet size:   {sum(sizes) / len(sizes):.2f} bytes")
print(f"Smallest packet size:  {min(sizes)} bytes")
print(f"Largest packet size:   {max(sizes)} bytes")
print(f"Packets / second:   {len(sizes) / duration:.2f}")