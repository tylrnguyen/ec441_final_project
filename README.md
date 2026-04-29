# EC441 Network Traffic Analysis

## Project structure

## Project Structure

```text
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
└── results/

Python scripts for analyzing network traffic from PCAP files (Netflix, Google Meet, Discord)

### VM Setup (Multipass)

# Start the VM
multipass start ec441

# Transfer the project to the VM
multipass transfer -r ~/<path to proj>/ec441_final_project ec441:/home/ubuntu/

# SSH into the VM
multipass shell ec441

# Navigate to scripts within the VM
cd /home/ubuntu/ec441_final_project

# Run the full analysis pipeline: 
python main.py

# After you're finished, stop the VM in a separate terminal
multipass stop ec441
```

## Parsers Overview

## TCP Parser

### Analyzes: 
- Retransmissions
- Window sizes 
- ACK RTT (if available)

## UDP Parser

### Analyzes: 
- Throughput
- Packet timing / jitter