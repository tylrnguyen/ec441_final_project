# extracts TCP retransmissions & window size
# retransmissions, window size, TCP ports, ACK RTT if available

from parsers.base_parser import BaseParser

class TCPParser(BaseParser):

    def parse(self):
        cap = self.capture(display_filter="tcp")

        total_tcp = 0
        total_bytes = 0
        retransmissions = 0
        window_sizes = []
        timestamps = []
        ack_rtts = []

        for packet in cap:
            total_tcp += 1

            # Frame length total packet size in bytes
            try:
                total_bytes += int(packet.length)
            except AttributeError:
                pass

            # timestamp used to compute capture duration / throughput
            try:
                timestamps.append(float(packet.sniff_timestamp))
            except AttributeError:
                pass

            # wireshark marks retransmissions with a special field, so they can be counted easily
            try:
                if hasattr(packet.tcp, "analysis_retransmission"):
                    retransmissions += 1
            except AttributeError:
                pass

            # tcp window size shows how much data receiver willing to accept
            try:
                window_sizes.append(int(packet.tcp.window_size_value))
            except AttributeError:
                pass

            # computed when possible
            # estimate RTT based on data packets and ACKS
            try:
                ack_rtts.append(float(packet.tcp.analysis_ack_rtt) * 1000)
            except AttributeError:
                pass

        try:
            cap.close()
        except Exception:
            pass

        # duration of TCP traffic in this capture
        duration = max(timestamps) - min(timestamps) if len(timestamps) > 1 else 0

        return {
            "total_tcp_packets": total_tcp,
            "total_tcp_bytes": total_bytes,
            "duration_sec": duration,
            "throughput_bytes_per_sec": total_bytes / duration if duration > 0 else None,
            "retransmissions": retransmissions,
            "average_window_size": sum(window_sizes) / len(window_sizes) if window_sizes else None,
            "average_ack_rtt_ms": sum(ack_rtts) / len(ack_rtts) if ack_rtts else None,
            "ack_rtt_samples_ms": ack_rtts[:500]
        }