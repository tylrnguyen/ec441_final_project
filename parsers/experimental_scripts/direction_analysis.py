import sys
import pyshark
import os

PCAP_FILES = {
    "netflix": "../data/netflix.pcap",
    "meet": "../data/meet.pcap",
    "discord": "../data/discord.pcap"
}

if len(sys.argv) < 2:
    print("Usage: python direction_analysis.py <netflix|meet|discord>")
    sys.exit(1)

app = sys.argv[1].lower()

if app not in PCAP_FILES:
    print("Unknown app")
    sys.exit(1)

PCAP = PCAP_FILES[app]

if not os.path.exists(PCAP):
    print("File not found")
    sys.exit(1)

cap = pyshark.FileCapture(PCAP)

upload = 0
download = 0

# detect local IP automatically
local_ip = None

for pkt in cap:
    try:
        if not local_ip:
            local_ip = pkt.ip.src
        
        if pkt.ip.src == local_ip:
            upload += 1
        else:
            download += 1

    except AttributeError:
        pass

total = upload + download

print(f"{app.capitalize()} Traffic Direction:")
print(f"Upload packets:   {upload} ({upload/total*100:.2f}%)")
print(f"Download packets: {download} ({download/total*100:.2f}%)")