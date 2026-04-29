#!/bin/bash
# usage: sudo bash capture.sh <app> <condition>
# ex:    sudo bash capture.sh meet latency

APP=$1
COND=$2
IFACE="en0"
DUR=180
OUTDIR="$(dirname "$0")/data"

if [ -z "$APP" ] || [ -z "$COND" ]; then
  echo "usage: sudo bash capture.sh <app> <condition>"
  echo "  app:  meet | hulu | discord"
  echo "  cond: normal | latency | loss"
  exit 1
fi

mkdir -p "$OUTDIR"
OUTFILE="$OUTDIR/${APP}_${COND}.pcapng"

PF_CONF="/tmp/netstress_pf.conf"

apply_impairment() {
  if [ "$COND" = "latency" ]; then
    echo "[+] adding 100ms latency"
    dnctl pipe 1 config delay 100
    printf "dummynet in all pipe 1\ndummynet out all pipe 1\n" > "$PF_CONF"
    pfctl -f "$PF_CONF" 2>/dev/null
    pfctl -e 2>/dev/null
  elif [ "$COND" = "loss" ]; then
    echo "[+] adding 2% packet loss"
    dnctl pipe 1 config plr 0.02
    printf "dummynet in all pipe 1\ndummynet out all pipe 1\n" > "$PF_CONF"
    pfctl -f "$PF_CONF" 2>/dev/null
    pfctl -e 2>/dev/null
  else
    echo "[+] no impairment (normal capture)"
  fi
}

clear_impairment() {
  pfctl -d 2>/dev/null
  dnctl -q flush
  rm -f "$PF_CONF"
  echo "[+] impairment cleared"
}

trap clear_impairment EXIT

echo "=== NetStress Capture ==="
echo "  app:       $APP"
echo "  condition: $COND"
echo "  interface: $IFACE"
echo "  duration:  ${DUR}s (3 min)"
echo "  output:    $OUTFILE"
echo ""
echo ">>> Open $APP on your laptop NOW, then press Enter to start <<<"
read -r

apply_impairment

# quick sanity check
if [ "$COND" != "normal" ]; then
  echo "[+] verifying impairment is active..."
  dnctl list
fi

echo "[+] capturing ${DUR}s... use $APP normally"
tshark -i "$IFACE" -w "$OUTFILE" -a duration:$DUR

clear_impairment

echo ""
echo "done: $OUTFILE ($(du -h "$OUTFILE" | cut -f1))"
