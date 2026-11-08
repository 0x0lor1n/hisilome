#!/usr/bin/env bash
# Summed over every mount: <audio> offers opus first, so listeners split.
# With METRICS_OUT set, the same fetch is also rendered as a node_exporter
# textfile: per-mount listeners and counters, peak, queue length, station up.

set -euo pipefail

ADMIN="${ADMIN:-admin:hackme}"
HOST="${HOST:-127.0.0.1:8000}"
OUT="${OUT:-radio/state/listeners.txt}"
METRICS_OUT="${METRICS_OUT:-}"
# icecast's <listener_peak> is per-mount and resets with the process.
PEAK_FILE="${PEAK_FILE:-$(dirname "$OUT")/listener-peak.txt}"
QUEUE_FILE="${QUEUE_FILE:-$(dirname "$OUT")/queue.m3u}"
# Empty while liquidsoap runs; ExecStopPost writes the offline <style> into it.
STATUS_FILE="${STATUS_FILE:-$(dirname "$OUT")/status.html}"
INTERVAL="${INTERVAL:-30}"
ONCE=0

[ "${1:-}" = "--once" ] && ONCE=1

# icecast's stats XML, one tag per line; empty when icecast is down.
fetch_stats() {
  curl -s --max-time 5 -u "$ADMIN" "http://${HOST}/admin/stats" 2>/dev/null |
    sed 's/</\n</g'
}

# Sum <listeners> over every <source> block.
count_listeners() {
  awk '
            /^<source mount=/ { inmount = 1 }
            inmount && /^<\/source>/ { inmount = 0 }
            inmount && /^<listeners>/ { gsub(/^<listeners>/, ""); cur += $0 }
            END { print cur+0 }
        '
}

read_peak() {
  local p
  p="$(cat "$PEAK_FILE" 2>/dev/null || true)"
  case "$p" in
  '' | *[!0-9]*) echo 0 ;;
  *) echo "$p" ;;
  esac
}

# Raise the stored peak if $1 exceeds it; echo the resulting peak.
update_peak() {
  local n="$1" peak tmp
  peak="$(read_peak)"
  if [ "$n" -gt "$peak" ] 2>/dev/null; then
    peak="$n"
    tmp="${PEAK_FILE}.tmp.$$"
    printf '%s\n' "$peak" >"$tmp"
    mv "$tmp" "$PEAK_FILE"
  fi
  echo "$peak"
}

render() {
  local n="$1" peak="$2"
  # A counter reading 1 advertises emptiness.
  if [ -n "$n" ] && [ "$n" -ge 2 ] 2>/dev/null; then
    printf '%s listening' "$n"
    # Not `&&`-chained: a false last test fails the function under set -e,
    # and the file never updated while count == peak.
    if [ "$peak" -gt "$n" ] 2>/dev/null; then
      printf ' · peak %s' "$peak"
    fi
  else
    printf 'connected'
    # Alone, but the room has been fuller: show the high-water mark.
    if [ "$peak" -ge 2 ] 2>/dev/null; then
      printf ' · peak %s' "$peak"
    fi
  fi
}

# Prometheus text format from the split stats on stdin. Counters are
# icecast's own (reset with the process; rate() copes).
render_metrics() {
  local peak="$1" icecast_up="$2" queue station
  queue="$(grep -c . "$QUEUE_FILE" 2>/dev/null || true)"
  queue="${queue:-0}"
  if [ -f "$STATUS_FILE" ] && [ ! -s "$STATUS_FILE" ]; then station=1; else station=0; fi
  awk -v peak="$peak" -v icecast_up="$icecast_up" -v queue="$queue" -v station="$station" '
    /^<source mount=/ {
      match($0, /mount="[^"]*"/)
      m = substr($0, RSTART + 7, RLENGTH - 8)
      inmount = 1
      mounts[m] = 1
    }
    inmount && /^<\/source>/ { inmount = 0 }
    inmount && /^<listeners>/            { sub(/^<listeners>/, "");            listeners[m] = $0 + 0 }
    inmount && /^<listener_connections>/ { sub(/^<listener_connections>/, ""); conns[m] = $0 + 0 }
    inmount && /^<total_bytes_sent>/     { sub(/^<total_bytes_sent>/, "");     sent[m] = $0 + 0 }
    inmount && /^<total_bytes_read>/     { sub(/^<total_bytes_read>/, "");     read_[m] = $0 + 0 }
    END {
      print "# HELP hisilome_icecast_up 1 if icecast answered /admin/stats."
      print "# TYPE hisilome_icecast_up gauge"
      print "hisilome_icecast_up " icecast_up
      print "# HELP hisilome_station_up 1 while liquidsoap feeds the mounts."
      print "# TYPE hisilome_station_up gauge"
      print "hisilome_station_up " station
      print "# HELP hisilome_queue_tracks Tracks in the current play queue."
      print "# TYPE hisilome_queue_tracks gauge"
      print "hisilome_queue_tracks " queue
      print "# HELP hisilome_listeners_peak Highest summed listener count seen since the peak file was last reset."
      print "# TYPE hisilome_listeners_peak gauge"
      print "hisilome_listeners_peak " peak
      print "# HELP hisilome_listeners Listeners connected to a mount."
      print "# TYPE hisilome_listeners gauge"
      for (m in mounts) printf "hisilome_listeners{mount=\"%s\"} %d\n", m, listeners[m]
      print "# HELP hisilome_listener_connections_total Listener connections icecast has accepted on a mount."
      print "# TYPE hisilome_listener_connections_total counter"
      for (m in mounts) printf "hisilome_listener_connections_total{mount=\"%s\"} %d\n", m, conns[m]
      print "# HELP hisilome_bytes_sent_total Bytes icecast has sent to listeners of a mount."
      print "# TYPE hisilome_bytes_sent_total counter"
      for (m in mounts) printf "hisilome_bytes_sent_total{mount=\"%s\"} %d\n", m, sent[m]
      print "# HELP hisilome_bytes_read_total Bytes icecast has read from the source of a mount."
      print "# TYPE hisilome_bytes_read_total counter"
      for (m in mounts) printf "hisilome_bytes_read_total{mount=\"%s\"} %d\n", m, read_[m]
    }
  '
}

write_once() {
  local stats n peak out tmp icecast_up=1
  stats="$(fetch_stats || true)"
  [ -n "$stats" ] || icecast_up=0
  n="$(count_listeners <<<"$stats" || true)"
  n="${n:-0}"
  mkdir -p "$(dirname "$OUT")"
  peak="$(update_peak "$n")"
  out="$(render "$n" "$peak")"
  tmp="${OUT}.tmp.$$"
  printf '%s' "$out" >"$tmp"
  mv "$tmp" "$OUT"

  if [ -n "$METRICS_OUT" ]; then
    mkdir -p "$(dirname "$METRICS_OUT")"
    tmp="${METRICS_OUT}.tmp.$$"
    render_metrics "$peak" "$icecast_up" <<<"$stats" >"$tmp"
    chmod 0644 "$tmp"
    mv "$tmp" "$METRICS_OUT"
  fi
}

if [ "$ONCE" -eq 1 ]; then
  write_once
  cat "$OUT"
  echo
  [ -z "$METRICS_OUT" ] || cat "$METRICS_OUT"
  exit 0
fi

while true; do
  write_once || true
  sleep "$INTERVAL"
done
