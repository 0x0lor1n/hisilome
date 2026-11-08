"""Radio state as the shell shows it: offline style, listener line, schedule.

Three writers feed `radio/state/`: `station-online`/`station-offline` flip
`status.html` between empty and `offlineStyle` (nix/packages.nix), which the
shell includes into <head>; `listener-count` renders icecast's stats into
`listeners.txt`; liquidsoap writes `schedule.html`, spliced into
/schedule.html and shown in the console's `.sc-frame`.

The browser tests write fixtures through `radio_state`. The listener-count
tests need no browser: the real binary (E2E_LISTENER_COUNT from the e2e env,
else bin/listener-count.sh) runs `--once` against a fake `admin/stats` on a
loopback port, writing into a temp dir, never into radio/state/.
"""

import http.server
import os
import re
import subprocess
import threading
from pathlib import Path

import pytest
from conftest import FIXTURES, REPO
from playwright.sync_api import expect


def test_offline_fixture_matches_station_offline():
    """`status-offline.html` must be byte-for-byte what station-offline writes."""
    nix = (REPO / "nix" / "packages.nix").read_text()
    m = re.search(r'offlineStyle = "(.*?)";', nix)
    assert m, "offlineStyle not found in nix/packages.nix"
    assert (FIXTURES / "status-offline.html").read_text() == m.group(1)


def _station_ui(page) -> str:
    return page.evaluate(
        "getComputedStyle(document.documentElement)"
        ".getPropertyValue('--station-ui').trim()"
    )


def test_offline_hides_station_ui(page, base, radio_state):
    radio_state.fixture("status.html", "status-offline.html")
    page.goto(base + "/")

    assert _station_ui(page) == "none"
    expect(page.locator(".console-meta")).to_be_hidden()
    expect(page.locator(".console-play")).to_be_hidden()
    # The <audio> is only hidden, not removed: coming back online needs no reload.
    assert page.locator("audio.console-audio").count() == 1
    # The live frame carries the loader crawl while down.
    anim = page.locator("iframe.console-live").evaluate(
        "f => getComputedStyle(f).animationName"
    )
    assert anim == "ld-crawl"


def test_online_restores_station_ui(page, base, radio_state):
    radio_state.fixture("status.html", "status-online.html")
    page.goto(base + "/")

    assert _station_ui(page) == ""
    expect(page.locator(".console-meta")).to_be_visible()
    expect(page.locator(".console-play")).to_be_visible()
    anim = page.locator("iframe.console-live").evaluate(
        "f => getComputedStyle(f).animationName"
    )
    assert anim == "none"


def test_offline_frame_says_so(page, base, radio_state):
    """station-offline + liquidsoap gone (no console.html): what a visitor sees."""
    radio_state.fixture("status.html", "status-offline.html")
    radio_state.remove("console.html")
    page.goto(base + "/")

    live = page.frame_locator("iframe.console-live")
    expect(live.locator(".rc-off")).to_have_text("station offline")
    assert live.locator(".rc-title").count() == 0
    expect(page.locator(".console-meta")).to_be_hidden()
    # The router is untouched by the radio being down.
    expect(page.locator("iframe.cur")).to_have_count(1)


def test_offline_toggle_without_reload_of_shell(page, base, radio_state, nav_token):
    """A route click after the state flips keeps the shell; only a load reads status."""
    radio_state.fixture("status.html", "status-online.html")
    page.goto(base + "/")
    nav_token.set()
    expect(page.locator(".console-meta")).to_be_visible()

    radio_state.fixture("status.html", "status-offline.html")
    page.locator("iframe.cur").element_handle().content_frame().locator(
        "a[href*='#']"
    ).first.click()
    page.wait_for_timeout(300)
    # SSI runs at document load: the shell still shows the state it loaded with.
    assert nav_token.kept()
    expect(page.locator(".console-meta")).to_be_visible()

    page.reload()
    expect(page.locator(".console-meta")).to_be_hidden()


def _stats_xml(*per_mount: int) -> str:
    srcs = "".join(
        f'<source mount="/stream.{m}"><listeners>{n}</listeners>'
        f"<listener_connections>{n * 10}</listener_connections>"
        f"<total_bytes_sent>{n * 1000}</total_bytes_sent>"
        f"<total_bytes_read>{n * 7}</total_bytes_read></source>"
        for m, n in zip(("opus", "mp3"), per_mount)
    )
    return f'<?xml version="1.0"?><icestats><admin>x</admin>{srcs}</icestats>'


class FakeIcecast:
    """Answers every GET with the current stats XML; `set(*listeners)` per mount."""

    def __init__(self):
        self.body = _stats_xml(0, 0).encode()
        srv = self

        class H(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/xml")
                self.send_header("Content-Length", str(len(srv.body)))
                self.end_headers()
                self.wfile.write(srv.body)

            def log_message(self, format, *args):
                pass

        self._srv = http.server.HTTPServer(("127.0.0.1", 0), H)
        self.host = f"127.0.0.1:{self._srv.server_address[1]}"
        threading.Thread(target=self._srv.serve_forever, daemon=True).start()

    def set(self, *per_mount: int):
        self.body = _stats_xml(*per_mount).encode()

    def close(self):
        self._srv.shutdown()


@pytest.fixture(scope="module")
def icecast():
    f = FakeIcecast()
    yield f
    f.close()


class ListenerCount:
    """Run `listener-count --once` into a private dir; return `listeners.txt`."""

    def __init__(self, tmp: Path, host: str):
        exe = os.environ.get("E2E_LISTENER_COUNT")
        self.cmd = [exe] if exe else ["bash", str(REPO / "bin" / "listener-count.sh")]
        self.tmp = tmp
        self.host = host
        self.out = tmp / "listeners.txt"
        self.peak = tmp / "listener-peak.txt"
        self.metrics = tmp / "metrics.prom"

    def once(self, host: str | None = None) -> str:
        env = dict(
            os.environ,
            HOST=host or self.host,
            ADMIN="e2e:e2e",
            OUT=str(self.out),
            METRICS_OUT=str(self.metrics),
        )
        r = subprocess.run(
            [*self.cmd, "--once"],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert r.returncode == 0, r.stderr
        return self.out.read_text()

    def peak_value(self) -> int:
        return int(self.peak.read_text()) if self.peak.exists() else 0

    def metric(self, name: str) -> dict[str, float]:
        """`name{labels} value` lines → {labels: value}; bare name → {"": value}."""
        out = {}
        for line in self.metrics.read_text().splitlines():
            m = re.match(rf"^{re.escape(name)}(\{{[^}}]*\}})? (\S+)$", line)
            if m:
                out[m.group(1) or ""] = float(m.group(2))
        return out


@pytest.fixture
def lc(tmp_path, icecast):
    return ListenerCount(tmp_path, icecast.host)


def test_listener_line_forms(lc, icecast):
    icecast.set(0, 0)
    assert lc.once() == "connected"
    assert not lc.peak.exists(), "a zero count must not create the peak file"

    # One listener reads as empty: the room never advertises a single soul.
    icecast.set(1, 0)
    assert lc.once() == "connected"

    icecast.set(2, 3)
    assert lc.once() == "5 listening"  # summed over mounts, peak == count: no suffix

    icecast.set(1, 1)
    assert lc.once() == "2 listening · peak 5"

    icecast.set(1, 0)
    assert lc.once() == "connected · peak 5"

    icecast.set(0, 0)
    assert lc.once() == "connected · peak 5"


def test_peak_is_monotonic(lc, icecast):
    icecast.set(5, 0)
    lc.once()
    assert lc.peak_value() == 5
    icecast.set(2, 0)
    assert lc.once() == "2 listening · peak 5"
    assert lc.peak_value() == 5
    icecast.set(4, 3)
    assert lc.once() == "7 listening"
    assert lc.peak_value() == 7


def test_peak_file_garbage_reads_as_zero(lc, icecast):
    lc.peak.write_text("seven\n")
    icecast.set(2, 0)
    assert lc.once() == "2 listening"
    assert lc.peak_value() == 2


def test_icecast_down_is_connected_and_flagged(lc, icecast):
    icecast.set(3, 0)
    lc.once()
    # Nothing listens on port 1; the fetch fails fast.
    assert lc.once(host="127.0.0.1:1") == "connected · peak 3"
    assert lc.metric("hisilome_icecast_up") == {"": 0.0}
    assert lc.metric("hisilome_listeners") == {}


def test_metrics_per_mount(lc, icecast):
    icecast.set(3, 2)
    lc.once()
    assert lc.metric("hisilome_icecast_up") == {"": 1.0}
    assert lc.metric("hisilome_listeners") == {
        '{mount="/stream.opus"}': 3.0,
        '{mount="/stream.mp3"}': 2.0,
    }
    assert lc.metric("hisilome_listener_connections_total") == {
        '{mount="/stream.opus"}': 30.0,
        '{mount="/stream.mp3"}': 20.0,
    }
    assert lc.metric("hisilome_listeners_peak") == {"": 5.0}
    # No status.html in the temp dir → station down; an empty one → up.
    assert lc.metric("hisilome_station_up") == {"": 0.0}
    (lc.tmp / "status.html").write_text("")
    lc.once()
    assert lc.metric("hisilome_station_up") == {"": 1.0}


def test_listeners_fragment_served_raw(page, base, radio_state):
    """What listener-count writes is what /listeners.txt returns, uncached."""
    radio_state.fixture("listeners.txt")
    r = page.request.get(base + "/listeners.txt")
    assert r.ok
    assert r.text() == "3 listening · peak 7"
    assert r.headers.get("content-type", "").startswith("text/plain")
    assert "no-store" in r.headers.get("cache-control", "")


def test_schedule_fragment_spliced(page, base, radio_state):
    radio_state.fixture("schedule.html")
    radio_state.fixture("refresh.html")
    page.goto(base + "/schedule.html")
    rows = page.locator("ul.sc-list > li")
    expect(rows).to_have_count(3)
    expect(rows.nth(1)).to_have_class("sc-now")
    expect(rows.nth(1).locator(".sc-w")).to_have_text("now")
    assert "E2E Fixture - Test Track" in rows.nth(1).locator(".sc-t").inner_text()
    # The frame reloads on liquidsoap's interval, like the live frame.
    assert page.locator("meta[http-equiv=refresh]").get_attribute("content") == "30"
    assert page.locator("title").count() == 1


def test_schedule_panel_in_console(page, base, radio_state):
    radio_state.fixture("console.html")
    radio_state.fixture("schedule.html")
    page.goto(base + "/")

    toggle = page.locator("details.sc-toggle")
    panel = page.locator(".sc-panel")
    expect(panel).to_be_hidden()

    toggle.locator("summary").click()
    expect(toggle).to_have_attribute("open", "")
    expect(panel).to_be_visible()

    frame = page.frame_locator("iframe.sc-frame")
    rows = frame.locator("ul.sc-list > li")
    expect(rows).to_have_count(3)
    expect(rows.nth(1)).to_have_class("sc-now")
    # The shell did not reload to show it.
    expect(page.locator("audio.console-audio")).to_have_count(1)

    toggle.locator("summary").click()
    expect(toggle).not_to_have_attribute("open", "")
    expect(panel).to_be_hidden()


def test_schedule_panel_hidden_when_folded(page, base, radio_state, console):
    radio_state.fixture("console.html")
    radio_state.fixture("schedule.html")
    page.goto(base + "/")
    toggle = page.locator("details.sc-toggle")
    toggle.locator("summary").click()
    expect(page.locator(".sc-panel")).to_be_visible()

    console.chevron.click()
    expect(console.fold).to_be_checked()
    expect(page.locator(".sc-panel")).to_be_hidden()
    # <details> stays open: unfolding brings the panel straight back.
    expect(toggle).to_have_attribute("open", "")
    console.chevron.click()
    expect(page.locator(".sc-panel")).to_be_visible()
