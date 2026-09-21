#!/usr/bin/env bash
# Listener count across every mount, as a display string for the console.
# The <audio> element offers opus first and mp3 second, so listeners split
# between the two; counting one mount undercounts the other's audience.

set -euo pipefail

ADMIN="${ADMIN:-admin:hackme}"
HOST="${HOST:-127.0.0.1:8000}"
OUT="${OUT:-radio/state/listeners.txt}"
INTERVAL="${INTERVAL:-30}"
ONCE=0

[ "${1:-}" = "--once" ] && ONCE=1

# Sum <listeners> and <listener_peak> over every <source> block. Peak is
# per-mount in icecast, so the sum is an upper bound, not a true peak.
count_listeners() {
  curl -s --max-time 5 -u "$ADMIN" "http://${HOST}/admin/stats" 2>/dev/null |
    sed 's/</\n</g' |
    awk '
            /^<source mount=/ { inmount = 1 }
            inmount && /^<\/source>/ { inmount = 0 }
            inmount && /^<listeners>/      { gsub(/^<listeners>/, "");      cur  += $0 }
            inmount && /^<listener_peak>/  { gsub(/^<listener_peak>/, ""); peak += $0 }
            END { print cur+0 "|" peak+0 }
        '
}

render() {
  local n="${1%%|*}" peak="${1##*|}"
  # A counter reading 1 advertises emptiness.
  if [ -n "$n" ] && [ "$n" -ge 2 ] 2>/dev/null; then
    printf '%s listening' "$n"
    # Not `&&`-chained: a false test as the last command fails the function
    # under set -e, and the file then never updates while the count is at
    # its peak — exactly when listeners are arriving.
    if [ -n "$peak" ] && [ "$peak" -gt "$n" ] 2>/dev/null; then
      printf ' (peak %s)' "$peak"
    fi
  else
    printf 'connected'
  fi
}

write_once() {
  local n out tmp
  n="$(count_listeners || true)"
  out="$(render "$n")"
  tmp="${OUT}.tmp.$$"
  mkdir -p "$(dirname "$OUT")"
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
