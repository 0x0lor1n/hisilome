#!/usr/bin/env bash
# Listener count across every mount, as a display string for the console.
# The <audio> element offers opus first and mp3 second, so listeners split
# between the two; counting one mount undercounts the other's audience.

set -euo pipefail

ADMIN="${ADMIN:-admin:hackme}"
HOST="${HOST:-127.0.0.1:8000}"
OUT="${OUT:-radio/state/listeners.txt}"
# All-time peak. icecast's own <listener_peak> is per-mount and resets with
# the process, so we keep our own maximum next to OUT. radio/state sits on
# the persistent volume (stateDir = /persist/radio in prod), so it survives
# reboots on the impermanent host; nothing else touches the file.
PEAK_FILE="${PEAK_FILE:-$(dirname "$OUT")/listener-peak.txt}"
INTERVAL="${INTERVAL:-30}"
ONCE=0

[ "${1:-}" = "--once" ] && ONCE=1

# Sum <listeners> over every <source> block.
count_listeners() {
  curl -s --max-time 5 -u "$ADMIN" "http://${HOST}/admin/stats" 2>/dev/null |
    sed 's/</\n</g' |
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
    # Not `&&`-chained: a false test as the last command fails the function
    # under set -e, and the file then never updates while the count is at
    # its peak - exactly when listeners are arriving.
    if [ "$peak" -gt "$n" ] 2>/dev/null; then
      printf ' (peak %s)' "$peak"
    fi
  else
    printf 'connected'
  fi
}

write_once() {
  local n peak out tmp
  n="$(count_listeners || true)"
  n="${n:-0}"
  mkdir -p "$(dirname "$OUT")"
  peak="$(update_peak "$n")"
  out="$(render "$n" "$peak")"
  tmp="${OUT}.tmp.$$"
  printf '%s' "$out" >"$tmp"
  mv "$tmp" "$OUT"
}

if [ "$ONCE" -eq 1 ]; then
  write_once
  cat "$OUT"
  echo
  exit 0
fi

while true; do
  write_once || true
  sleep "$INTERVAL"
done
