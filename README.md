# EC441 Network Traffic Analysis

## Project structure

ec441_final_project/
│
├── README.md
│
├── data/
│   ├── netflix.pcap
│   ├── meet.pcap
│   ├── discord.pcap
│
├── scripts/
│   ├── analyze_protocols.py
│   ├── packet_stats.py
│   ├── dns_analysis.py
│   ├── direction_analysis.py
│   
│
└──results/

Python scripts for analyzing network traffic from PCAP files (Netflix, Google Meet, Discord)

### VM Setup (Multipass)
```bash
# Start the VM
multipass start ec441

# Transfer the project to the VM
multipass transfer -r ~/Dev/EC441/ec441_final_project ec441:/home/ubuntu/

# SSH into the VM
multipass shell ec441

# Navigate to scripts
cd /home/ubuntu/ec441_final_project/scripts
```

## Scripts Overview

All three scripts analyze PCAP files and can be run from the scripts directory:

python <scipt file>.py <app name>           

Each script takes an app name as argument: `netflix`, `meet`, or `discord`.

### analyze_protocols.py
**Purpose:** Understand what network protocols dominate the traffic.

**What it analyzes:**
- Total packet count
- TCP packet count and percentage
- UDP packet count and percentage
- Top 10 protocols by frequency (IP, TCP, TLS, HTTP, etc.)

**Why:** Shows whether an application relies on reliable (TCP) or faster unreliable (UDP) transmission, and identifies encrypted traffic (TLS) vs unencrypted traffic.

### packet_stats.py
**Purpose:** Measure traffic volume and size characteristics.

**What it analyzes:**
- Total number of packets captured
- How long the capture lasted in seconds
- Average packet size
- Smallest and largest packet sizes
- Traffic intensity / packets per second

**Why:** Helps estimate bandwidth usage, understand traffic patterns, and detect anomalies like unusually large packets.

### dns_analysis.py
**Purpose:** Identify all external servers an application communicates with.

**What it analyzes:**
- All unique DNS queries 
- Lists them in alphabetical order
- Shows if no DNS traffic was captured

**Why:** Reveals tracking services, CDN endpoints, and cloud services that an application depends on. Useful for privacy analysis and understanding service dependencies.

### direction_analysis,py
**What it analyzes:** 
Determines whether packets are upload (client to server) or download (server to client) and calculates the percentage

**Why:**
Shows communication patterns, not just how data is sent but who is sending it