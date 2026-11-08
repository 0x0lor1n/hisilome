# Fixture fragments

Stand-ins for what liquidsoap and `listener-count` write to `radio/state/`.
Tests install them through the `radio_state` fixture (conftest.py), which puts
the real files back on teardown, so a run never leaves the dev stack in a
fixture state.

| file | stands in for | note |
| --- | --- | --- |
| `console.html` | liquidsoap `write_console` | `.rc-ls` is baked in by liquidsoap, not included separately |
| `refresh.html`, `refresh-fast.html` | liquidsoap `write_refresh` | the fast one reloads the live frame every second |
| `schedule.html` | liquidsoap `write_schedule` | three rows, middle one `.sc-now` |
| `listeners.txt`, `now-playing.txt` | `listener-count`, liquidsoap | plain text |
| `status-online.html` (empty), `status-offline.html` | `station-online` / `station-offline` | the offline one must equal `offlineStyle` in nix/packages.nix |
