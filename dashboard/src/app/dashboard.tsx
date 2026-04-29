"use client";

import { useState, useMemo } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell,
  Area, AreaChart, ComposedChart,
} from "recharts";

interface Win {
  window_index: number;
  time_sec: number;
  packet_count: number;
  bytes: number;
  throughput_kbps: number;
  protocols: Record<string, number>;
  retransmissions?: number;
  dup_acks?: number;
  avg_window_size?: number;
  avg_jitter_ms?: number;
}

interface TcpSum {
  total_retransmissions: number;
  total_dup_acks: number;
  total_fast_retransmits: number;
  total_out_of_order: number;
  retransmission_rate_pct: number;
  avg_window_size: number;
}

interface UdpSum {
  total_udp_packets: number;
  total_tcp_packets: number;
  udp_ratio_pct: number;
  avg_inter_arrival_ms: number;
  jitter_stdev_ms: number;
  avg_packet_size: number;
  median_packet_size: number;
}

interface Capture {
  label: string;
  file: string;
  packets_processed: number;
  duration_sec: number;
  total_bytes: number;
  avg_throughput_kbps: number;
  protocol_distribution: Record<string, number>;
  timeseries: Win[];
  tcp_summary?: TcpSum;
  udp_summary?: UdpSum;
}

interface DashData {
  apps: Record<string, Record<string, Capture>>;
  summary: Array<Record<string, unknown>>;
}

const APPS: Record<string, { name: string; type: "tcp" | "udp"; icon: string; color: string }> = {
  meet: { name: "Google Meet", type: "udp", icon: "🎥", color: "#4285F4" },
  hulu: { name: "Hulu", type: "tcp", icon: "📺", color: "#1CE783" },
  discord: { name: "Discord", type: "udp", icon: "🎮", color: "#5865F2" },
};

const CONDS: Record<string, string> = {
  normal: "Normal",
  latency: "+100ms Latency",
  loss: "2% Packet Loss",
};

const PIE_CLR = ["#0088FE", "#FF6B6B", "#00C49F", "#FFBB28", "#FF8042", "#A28BFF", "#FF6EC7"];
const COND_CLR: Record<string, string> = { normal: "#22c55e", latency: "#f59e0b", loss: "#ef4444" };

const ttStyle = {
  background: "#1a1a2e",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 8,
  color: "#fff",
  fontSize: 12,
};

function Stat({ label, val, unit, accent }: { label: string; val: string | number; unit: string; accent?: string }) {
  return (
    <div className="rounded-xl border border-white/[0.08] bg-white/[0.04] px-[18px] py-[14px] min-w-[140px] flex-1">
      <div className="text-[11px] text-white/45 uppercase tracking-wider mb-1">{label}</div>
      <div className="text-[26px] font-bold font-mono" style={{ color: accent || "#fff" }}>
        {val}<span className="text-[13px] font-normal text-white/40 ml-1">{unit}</span>
      </div>
    </div>
  );
}

function ProtoChart({ data }: { data: Record<string, number> }) {
  const entries = Object.entries(data).map(([name, value]) => ({ name, value }));
  const total = entries.reduce((s, e) => s + e.value, 0);
  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie data={entries} cx="50%" cy="50%" innerRadius={50} outerRadius={85}
          paddingAngle={2} dataKey="value" stroke="none">
          {entries.map((_, i) => <Cell key={i} fill={PIE_CLR[i % PIE_CLR.length]} />)}
        </Pie>
        <Tooltip contentStyle={ttStyle}
          formatter={(v) => `${total > 0 ? ((Number(v) / total) * 100).toFixed(1) : 0}%`} />
        <Legend wrapperStyle={{ fontSize: 11, color: "rgba(255,255,255,0.6)" }} />
      </PieChart>
    </ResponsiveContainer>
  );
}

function Card({ title, children, full = false }: { title: string; children: React.ReactNode; full?: boolean }) {
  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] pt-5 px-5 pb-3"
      style={full ? { gridColumn: "1 / -1" } : undefined}>
      <h3 className="text-sm font-bold text-white/70 mb-4" style={{ fontFamily: "var(--font-playfair), serif" }}>{title}</h3>
      {children}
    </div>
  );
}

export default function NetStressDashboard({ initialData }: { initialData: DashData }) {
  const data = initialData.apps;
  const [app, setApp] = useState("meet");
  const [cond, setCond] = useState("normal");
  const [cmp, setCmp] = useState(false);

  const avail = Object.keys(data).filter((k) => k in APPS);
  const meta = APPS[app];
  const cur: Capture | undefined = data[app]?.[cond];
  const tcp = meta?.type === "tcp";

  const conds = useMemo(() => {
    if (!data[app]) return [];
    return Object.keys(data[app]).filter((k) => k in CONDS);
  }, [data, app]);

  const overlay = useMemo(() => {
    if (!cmp || !data[app]) return null;
    const c = data[app];
    const n = c.normal?.timeseries || [];
    const l = c.latency?.timeseries || [];
    const lo = c.loss?.timeseries || [];
    const mx = Math.max(n.length, l.length, lo.length);
    return Array.from({ length: mx }, (_, i) => ({
      time_sec: n[i]?.time_sec ?? l[i]?.time_sec ?? lo[i]?.time_sec ?? i,
      normal: n[i]?.throughput_kbps ?? 0,
      latency: l[i]?.throughput_kbps ?? 0,
      loss: lo[i]?.throughput_kbps ?? 0,
    }));
  }, [cmp, app, data]);

  const bars = useMemo(() => {
    return avail.map((k) => {
      const row: Record<string, string | number> = { app: APPS[k].name };
      for (const c of Object.keys(CONDS)) {
        row[c] = data[k]?.[c]?.avg_throughput_kbps ?? 0;
      }
      return row;
    });
  }, [data, avail]);

  if (!cur) {
    return (
      <div className="flex items-center justify-center h-screen text-white/60">
        No data. Run <code className="mx-1 font-mono text-white/80">python main.py</code> with pcap files in data/
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* header */}
      <div className="px-8 pt-7 pb-5 border-b border-white/[0.06] bg-black/30">
        <div className="flex items-center gap-3 mb-1.5">
          <div>
            <h1 className="text-[26px] font-black tracking-tight text-white" style={{ fontFamily: "var(--font-playfair), serif" }}>NetStress</h1>
            <p className="text-xs text-white/35">Application Transport Under Duress | EC 441</p>
          </div>
        </div>
      </div>

      {/* controls */}
      <div className="px-8 py-4 flex flex-wrap gap-4 items-center border-b border-white/[0.04]">
        <div className="flex gap-1.5">
          {avail.map((k) => (
            <button key={k} onClick={() => setApp(k)}
              className="px-4 py-2 rounded-lg border-none cursor-pointer text-[13px] font-semibold transition-all"
              style={{
                background: app === k ? APPS[k].color : "rgba(255,255,255,0.06)",
                color: app === k ? "#fff" : "rgba(255,255,255,0.5)",
              }}>
              {APPS[k].icon} {APPS[k].name}
            </button>
          ))}
        </div>
        <div className="w-px h-7 bg-white/[0.08]" />
        <div className="flex gap-0.5 bg-white/[0.04] rounded-lg p-0.5">
          {conds.map((k) => {
            const on = !cmp && cond === k;
            return (
              <button key={k} onClick={() => { setCond(k); setCmp(false); }}
                className="px-3.5 py-[7px] rounded-md border cursor-pointer text-xs font-medium transition-all"
                style={{
                  background: on ? COND_CLR[k] + "22" : "transparent",
                  color: on ? COND_CLR[k] : "rgba(255,255,255,0.4)",
                  borderColor: on ? COND_CLR[k] + "44" : "transparent",
                }}>
                {CONDS[k]}
              </button>
            );
          })}
        </div>
        <button onClick={() => setCmp(!cmp)}
          className="px-3.5 py-[7px] rounded-md border-none cursor-pointer text-xs font-semibold transition-all"
          style={{
            background: cmp ? "#6366f1" : "rgba(255,255,255,0.06)",
            color: cmp ? "#fff" : "rgba(255,255,255,0.4)",
          }}>
          ⚖ Compare All
        </button>
      </div>

      {/* stats */}
      <div className="px-8 py-4 flex gap-3 flex-wrap">
        <Stat label="Avg Throughput" val={cur.avg_throughput_kbps.toLocaleString()} unit="Kbps" accent={meta.color} />
        <Stat label="Packets" val={cur.packets_processed.toLocaleString()} unit="total" />
        <Stat label="Duration" val={cur.duration_sec} unit="sec" />
        {tcp && cur.tcp_summary && (
          <>
            <Stat label="Retransmit Rate" val={cur.tcp_summary.retransmission_rate_pct} unit="%"
              accent={cur.tcp_summary.retransmission_rate_pct > 1 ? "#ef4444" : "#22c55e"} />
            <Stat label="Avg Window" val={(cur.tcp_summary.avg_window_size / 1024).toFixed(1)} unit="KB" />
          </>
        )}
        {!tcp && cur.udp_summary && (
          <>
            <Stat label="Avg Jitter" val={cur.udp_summary.avg_inter_arrival_ms} unit="ms"
              accent={cur.udp_summary.avg_inter_arrival_ms > 15 ? "#ef4444" : "#22c55e"} />
            <Stat label="UDP Ratio" val={cur.udp_summary.udp_ratio_pct} unit="%" />
          </>
        )}
      </div>

      {/* charts */}
      <div className="px-8 pb-8 pt-2 grid grid-cols-2 gap-4">
        {/* throughput */}
        <Card title={cmp ? "Throughput Comparison — All Conditions" : "Throughput Over Time"} full={cmp}>
          <ResponsiveContainer width="100%" height={260}>
            {cmp && overlay ? (
              <LineChart data={overlay}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="time_sec" stroke="rgba(255,255,255,0.2)" tick={{ fontSize: 10 }}
                  label={{ value: "Time (s)", position: "insideBottom", offset: -5, fill: "rgba(255,255,255,0.3)", fontSize: 10 }} />
                <YAxis stroke="rgba(255,255,255,0.2)" tick={{ fontSize: 10 }}
                  label={{ value: "Kbps", angle: -90, position: "insideLeft", fill: "rgba(255,255,255,0.3)", fontSize: 10 }} />
                <Tooltip contentStyle={ttStyle} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Line type="monotone" dataKey="normal" stroke={COND_CLR.normal} strokeWidth={2} dot={false} name="Normal" />
                <Line type="monotone" dataKey="latency" stroke={COND_CLR.latency} strokeWidth={2} dot={false} name="+100ms Latency" />
                <Line type="monotone" dataKey="loss" stroke={COND_CLR.loss} strokeWidth={2} dot={false} name="2% Loss" />
              </LineChart>
            ) : (
              <AreaChart data={cur.timeseries}>
                <defs>
                  <linearGradient id="tpGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={meta.color} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={meta.color} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="time_sec" stroke="rgba(255,255,255,0.2)" tick={{ fontSize: 10 }}
                  label={{ value: "Time (s)", position: "insideBottom", offset: -5, fill: "rgba(255,255,255,0.3)", fontSize: 10 }} />
                <YAxis stroke="rgba(255,255,255,0.2)" tick={{ fontSize: 10 }}
                  label={{ value: "Kbps", angle: -90, position: "insideLeft", fill: "rgba(255,255,255,0.3)", fontSize: 10 }} />
                <Tooltip contentStyle={ttStyle} />
                <Area type="monotone" dataKey="throughput_kbps" stroke={meta.color}
                  fill="url(#tpGrad)" strokeWidth={2} dot={false} name="Throughput" />
              </AreaChart>
            )}
          </ResponsiveContainer>
        </Card>

        {/* protocol dist */}
        {!cmp && (
          <Card title="Protocol Distribution">
            <ProtoChart data={cur.protocol_distribution} />
          </Card>
        )}

        {/* tcp retransmissions */}
        {tcp && (
          <Card title="TCP Retransmissions">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={cur.timeseries}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="time_sec" stroke="rgba(255,255,255,0.2)" tick={{ fontSize: 10 }} />
                <YAxis stroke="rgba(255,255,255,0.2)" tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={ttStyle} />
                <Bar dataKey="retransmissions" fill="#ef4444" radius={[2, 2, 0, 0]} name="Retransmissions" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        )}

        {/* tcp window size */}
        {tcp && (
          <Card title="TCP Window Size">
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={cur.timeseries}>
                <defs>
                  <linearGradient id="winGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="time_sec" stroke="rgba(255,255,255,0.2)" tick={{ fontSize: 10 }} />
                <YAxis stroke="rgba(255,255,255,0.2)" tick={{ fontSize: 10 }}
                  tickFormatter={(v) => `${(Number(v) / 1024).toFixed(0)}K`} />
                <Tooltip contentStyle={ttStyle} formatter={(v) => `${(Number(v) / 1024).toFixed(1)} KB`} />
                <Area type="monotone" dataKey="avg_window_size" stroke="#6366f1"
                  fill="url(#winGrad)" strokeWidth={2} dot={false} name="Window Size" />
              </AreaChart>
            </ResponsiveContainer>
          </Card>
        )}

        {/* udp jitter */}
        {!tcp && (
          <Card title="Inter-Arrival Jitter">
            <ResponsiveContainer width="100%" height={220}>
              <ComposedChart data={cur.timeseries}>
                <defs>
                  <linearGradient id="jGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="time_sec" stroke="rgba(255,255,255,0.2)" tick={{ fontSize: 10 }} />
                <YAxis stroke="rgba(255,255,255,0.2)" tick={{ fontSize: 10 }}
                  label={{ value: "ms", angle: -90, position: "insideLeft", fill: "rgba(255,255,255,0.3)", fontSize: 10 }} />
                <Tooltip contentStyle={ttStyle} formatter={(v) => `${Number(v)} ms`} />
                <Area type="monotone" dataKey="avg_jitter_ms" stroke="#f59e0b"
                  fill="url(#jGrad)" strokeWidth={2} dot={false} name="Jitter" />
              </ComposedChart>
            </ResponsiveContainer>
          </Card>
        )}

        {/* udp pkt rate */}
        {!tcp && (
          <Card title="Packet Rate">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={cur.timeseries}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="time_sec" stroke="rgba(255,255,255,0.2)" tick={{ fontSize: 10 }} />
                <YAxis stroke="rgba(255,255,255,0.2)" tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={ttStyle} />
                <Bar dataKey="packet_count" fill={meta.color} radius={[2, 2, 0, 0]} opacity={0.7} name="Packets/sec" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        )}

        {/* cross app summary */}
        <Card title="Cross-App Throughput (Kbps)" full>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={bars} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="app" stroke="rgba(255,255,255,0.3)" tick={{ fontSize: 12 }} />
              <YAxis stroke="rgba(255,255,255,0.2)" tick={{ fontSize: 10 }} />
              <Tooltip contentStyle={ttStyle} formatter={(v) => `${Number(v).toLocaleString()} Kbps`} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="normal" fill={COND_CLR.normal} radius={[3, 3, 0, 0]} name="Normal" />
              <Bar dataKey="latency" fill={COND_CLR.latency} radius={[3, 3, 0, 0]} name="+100ms Latency" />
              <Bar dataKey="loss" fill={COND_CLR.loss} radius={[3, 3, 0, 0]} name="2% Packet Loss" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* findings */}
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] px-6 py-5" style={{ gridColumn: "1 / -1" }}>
          <h3 className="text-sm font-bold text-white/70 mb-3" style={{ fontFamily: "var(--font-playfair), serif" }}>Key Findings</h3>
          <div className="grid grid-cols-3 gap-4">
            {avail.map((k) => {
              const m = APPS[k];
              const n = data[k]?.normal;
              const lo = data[k]?.loss;
              if (!n || !lo) return null;
              const drop = Math.round((1 - lo.avg_throughput_kbps / n.avg_throughput_kbps) * 100);
              return (
                <div key={k} className="p-3.5 bg-white/[0.02] rounded-lg"
                  style={{ border: `1px solid ${m.color}33` }}>
                  <div className="text-[13px] font-semibold mb-2" style={{ color: m.color }}>
                    {m.icon} {m.name}
                  </div>
                  <div className="text-xs text-white/55 leading-relaxed">
                    {m.type === "tcp"
                      ? `TCP dominant. Under 2% loss, throughput drops ~${drop}% as congestion control backs off. Retransmission rate: ${n.tcp_summary?.retransmission_rate_pct}% → ${lo.tcp_summary?.retransmission_rate_pct}%. Window size contracts.`
                      : `UDP dominant. Under 2% loss, throughput drops ~${drop}% but app adapts at application layer${k === "meet" ? " (codec bitrate, FEC)" : ""}. Jitter: ${n.udp_summary?.avg_inter_arrival_ms}ms → ${lo.udp_summary?.avg_inter_arrival_ms}ms.`}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
