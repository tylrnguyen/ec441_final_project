# base class
import pyshark
from pathlib import Path

"""
shared logic for opening PCAPNG file w/ pyshark

don't have to repeat FileCapture logic in each parser
"""

class BaseParser:
    def __init__(self, pcap_file):
        # Convert string path into a Path object so .exists() works
        self.pcap_file = Path(pcap_file)

        if not self.pcap_file.exists():
            raise FileNotFoundError(f"File not found: {self.pcap_file}")

    # open pcapng w/ optional display filter from wireshark
    def capture(self, display_filter=None):
        return pyshark.FileCapture(str(self.pcap_file), display_filter=display_filter, keep_packets=False)