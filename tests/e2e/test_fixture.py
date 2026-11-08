"""The `radio_state` fixture: nginx serves what it writes, teardown restores.

Not a shell test. It proves the mechanism Phase 2 relies on: a fragment
written under radio/state/ shows up through nginx (SSI on the live frame, the
raw fragment path too) with no caching in between, and the real files come
back untouched. `now-playing.txt` is the fragment, status is checked through
the live frame since the raw fragment is empty when online.
"""

import hashlib

import pytest
from conftest import FRAGMENTS, STATE_DIR


def _digest():
    h = hashlib.sha256()
    for name in FRAGMENTS:
        p = STATE_DIR / name
        h.update(name.encode())
        h.update(p.read_bytes() if p.exists() else b"<absent>")
    return h.hexdigest()


@pytest.fixture
def snapshot(radio_state):
    """Digest before the test, restore and compare after it.

    Calls restore() itself: pytest tears fixtures down in reverse setup
    order, so without it this would run before `radio_state` restores.
    """
    before = _digest()
    yield
    radio_state.restore()
    assert _digest() == before, "radio_state teardown did not restore radio/state/"


def test_fixture_served_and_restored(page, base, radio_state, snapshot):
    radio_state.fixture("console.html")
    radio_state.fixture("now-playing.txt")

    r = page.request.get(base + "/now-playing.txt")
    assert r.ok and r.text() == "E2E Fixture - Test Track"
    assert "no-store" in r.headers.get("cache-control", "")

    page.goto(base + "/live.html")
    assert page.locator(".rc-title").inner_text() == "E2E Fixture - Test Track"
    assert page.locator(".rc-ls").inner_text().strip() == "· 3 listening · peak 7"


def test_absent_console_shows_offline_stub(page, base, radio_state, snapshot):
    radio_state.remove("console.html")
    page.goto(base + "/live.html")
    assert page.locator(".rc-off").inner_text() == "station offline"
    assert page.locator(".rc-title").count() == 0


def test_offline_style_hides_station_ui(page, base, radio_state, snapshot):
    radio_state.fixture("status.html", "status-offline.html")
    page.goto(base + "/")
    ui = page.evaluate(
        "getComputedStyle(document.documentElement).getPropertyValue('--station-ui').trim()"
    )
    assert ui == "none"
    assert not page.locator(".console-meta").is_visible()

    radio_state.fixture("status.html", "status-online.html")
    page.goto(base + "/")
    assert page.locator(".console-meta").is_visible()
