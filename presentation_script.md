# NetStress — Presentation Script

## Slide 1: Title

Hi everyone, our project is called NetStress: Application Transport Under Duress. We set out to answer a straightforward question — when your network gets worse, what actually happens to the traffic of the apps you use every day?

## Slide 2: Motivation

We all know what bad network conditions feel like — laggy video calls, buffering on streaming. But what's happening at the transport layer? TCP and UDP handle degradation very differently, and different applications make very different choices about which protocols to use and how to adapt. We wanted to capture real traffic and see those differences firsthand.

## Slide 3: Experiment Setup

We tested three applications — Google Meet, Hulu, and Discord — each representing a different use case: video conferencing, streaming video, and voice/screen-sharing.

We ran each app on a VM using Multipass and captured traffic with Wireshark into PCAP files. For each app, we captured under three conditions: normal network, 100 milliseconds of added latency, and 2% packet loss. Each capture ran for about three minutes of active use.

## Slide 4: Analysis Pipeline

We built a Python pipeline to parse the PCAP files. There's a base parser that handles windowing and protocol classification, and then specialized parsers for TCP and UDP. The TCP parser extracts retransmissions, duplicate ACKs, and window sizes. The UDP parser tracks inter-arrival jitter and packet size distribution. Everything outputs to JSON, which feeds into a live dashboard built with Next.js and Recharts.

## Slide 5: Google Meet — UDP-Dominant

Starting with Google Meet. Under normal conditions, Meet sends at about 2,000 Kbps with 98% UDP traffic — mostly raw UDP and RTP for audio/video, with a small amount of STUN for NAT traversal.

When we add 100ms latency, throughput crashes to 343 Kbps — an 83% drop. Jitter jumps from 34 milliseconds to 334. The app is still using UDP, but it's aggressively reducing its codec bitrate to compensate.

Under 2% packet loss, throughput drops to 739 Kbps — a 64% drop. Jitter lands at 164ms. Meet adapts at the application layer using techniques like forward error correction rather than relying on the transport to retransmit.

The key takeaway: Meet stays on UDP but makes dramatic quality trade-offs to keep the call alive.

## Slide 6: Hulu — TCP-Dominant

Hulu is almost entirely TCP with TLS. Under normal conditions, it streams at about 3,300 Kbps with a retransmission rate of only 0.085%.

With added latency, throughput drops to 2,163 Kbps — about a 35% decrease. The retransmission rate climbs to 0.337%. The higher RTT means TCP's congestion window grows more slowly, reducing throughput.

Under 2% packet loss, something interesting happens — measured throughput actually goes up to 4,111 Kbps, but the retransmission rate jumps to 1.6%. This is likely TCP retransmitting aggressively, plus Hulu's adaptive bitrate algorithm buffering more data to stay ahead of drops. The raw byte count increases, but the user isn't actually getting more video — some of that bandwidth is wasted on retransmissions.

## Slide 7: Discord — Protocol Switching

Discord had the most interesting behavior. Normally, it's 97% UDP at about 4,875 Kbps with only 11ms of jitter — very clean.

Under latency, two things happen. Throughput drops to 1,364 Kbps, but more notably, the UDP ratio collapses from 97% to just 25%. Discord is falling back from UDP-based voice transport to TCP-based connections. Jitter spikes to 503ms.

Under packet loss, throughput stays relatively high at 4,288 Kbps, but the UDP ratio is still only 26%. Discord appears to shift traffic to TCP under adverse conditions — a fundamentally different strategy from Meet, which stays on UDP and degrades quality instead.

## Slide 8: Cross-App Comparison

*[Show the cross-app throughput bar chart]*

Looking across all three apps, the patterns are clear. Latency hurts UDP-dominant apps the most — Meet and Discord see the biggest throughput drops. Packet loss hits TCP apps differently than UDP apps — Hulu's congestion control mechanism kicks in, while Meet just reduces quality.

The protocol distribution shift in Discord is the standout finding. It shows that modern applications don't just pick TCP or UDP — they dynamically switch strategies based on network conditions.

## Slide 9: Key Takeaways

Three main takeaways:

First, TCP and UDP degrade differently under stress, exactly as the theory predicts. TCP backs off with congestion control. UDP keeps sending but the application has to handle the consequences.

Second, real applications are more nuanced than textbook examples. Discord switches protocols entirely. Meet adjusts codec parameters. Hulu's adaptive bitrate interacts with TCP congestion control in non-obvious ways.

Third, measuring at the transport layer reveals behaviors you can't see from the user experience alone — like Hulu's increased byte count under loss, or Discord's protocol fallback.

## Slide 10: Demo

Let me pull up the live dashboard so you can explore the data interactively.

*[Switch to localhost:3000, click through apps and conditions, show the compare mode]*
