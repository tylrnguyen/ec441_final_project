# extracts UDP jitter & throughput
# UDP ports

from parsers.base_parser import BaseParser


class UDPParser(BaseParser):
    def parse(self):
        cap = self.capture(display_filter="udp")

        udp_packets = 0
        total_bytes = 0

        timestamps = []
        sizes = []

        for pkt in cap:
            udp_packets += 1

            try:
                size = int(pkt.length)
                ts = float(pkt.sniff_timestamp)

                sizes.append(size)
                timestamps.append(ts)
                total_bytes += size
            except AttributeError:
                pass

        try:
            cap.close()
        except Exception:
            pass

        duration = max(timestamps) - min(timestamps) if len(timestamps) > 1 else 0

        # time gap between consecutive packets
        inter_arrivals = [
            timestamps[i] - timestamps[i - 1]
            for i in range(1, len(timestamps))
        ]

        # average change between consecutive arrival times
        avg_jitter_ms = (
            sum(abs(inter_arrivals[i] - inter_arrivals[i - 1]) for i in range(1, len(inter_arrivals)))
            / (len(inter_arrivals) - 1) * 1000
            if len(inter_arrivals) > 1
            else None
        )

        return {
            "total_udp_packets": udp_packets,
            "total_udp_bytes": total_bytes,
            "duration_sec": duration,
            "throughput_bytes_per_sec": total_bytes / duration if duration > 0 else None,
            "avg_udp_packet_size": sum(sizes) / len(sizes) if sizes else None,
            "avg_jitter_ms": avg_jitter_ms
        }