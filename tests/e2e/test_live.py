"""The live frame (`templates/live.html`): reloads itself, the shell does not.

liquidsoap writes `refresh.html` with the seconds left on the track and
`console.html` with the title/album/progress bar; nginx splices both into
/live.html by SSI. The frame is what reloads so that the shell -- and with it
the <audio> -- never does. These tests pin that split and that the fixture
fragments land in the frame as written.

Fragments come from `radio_state` (liquidsoap and listener-count are held
still for the session); `refresh-fast.html` reloads the frame every second.
"""

from playwright.sync_api import expect

LIVE = "iframe.console-live"


def _live_frame(page):
    return page.frame_locator(LIVE)


def _frame_token(page, value: str | None = None):
    """Set (value given) or read `window.__t` inside the live frame's document."""
    frame = page.locator(LIVE).element_handle().content_frame()
    assert frame is not None
    if value is not None:
        frame.evaluate("t => { window.__t = t }", value)
    return frame.evaluate("() => window.__t")


def test_refresh_reloads_frame_not_shell(page, base, radio_state, nav_token):
    radio_state.fixture("console.html")
    radio_state.fixture("refresh.html", "refresh-fast.html")
    page.goto(base + "/")
    expect(_live_frame(page).locator(".rc-title")).to_be_visible()

    nav_token.set()
    _frame_token(page, "live-" + nav_token.value)

    # content="1": the frame document is gone within ~1 s, 2 s is the bound.
    page.wait_for_function(
        """([el, t]) => el.contentWindow.__t !== t""",
        arg=[page.locator(LIVE).element_handle(), "live-" + nav_token.value],
        timeout=2_000,
    )
    assert nav_token.kept(), "the shell reloaded with the live frame"
    # Still the same document, with the fixture, after the reload.
    expect(_live_frame(page).locator(".rc-title")).to_have_text(
        "E2E Fixture - Test Track"
    )


def test_refresh_fallback_when_fragment_absent(page, base, radio_state):
    """Without refresh.html the stub keeps the frame reloading (10 s); without
    the stub nginx would splice its 404 page into <head>."""
    radio_state.remove("refresh.html")
    page.goto(base + "/")
    meta = _live_frame(page).locator('meta[http-equiv="refresh"]')
    expect(meta).to_have_count(1)
    expect(meta).to_have_attribute("content", "10")
    assert _live_frame(page).locator("title").count() == 1  # no 404 page in <head>


def test_console_fixture_renders_in_frame(page, base, radio_state):
    radio_state.fixture("console.html")
    radio_state.fixture("refresh.html")
    radio_state.fixture("listeners.txt")
    page.goto(base + "/")
    live = _live_frame(page)
    expect(live.locator(".rc-title")).to_have_text("E2E Fixture - Test Track")
    expect(live.locator(".rc-sub")).to_have_text("Fixture Album")
    expect(live.locator(".rc-bar .rc-fill")).to_be_visible()
    expect(live.locator(".rc-clock")).to_contain_text("/ 2:00")
    # The listener line is baked into console.html by liquidsoap from
    # listeners.txt; the two must agree or the console lies about the room.
    listeners = page.request.get(base + "/listeners.txt").text().strip()
    expect(live.locator(".rc-ls")).to_have_text("· " + listeners)
    # The frame is not the route frame: no shell inside it.
    assert live.locator("section.console").count() == 0


def test_offline_stub_in_frame_shell_intact(page, base, radio_state):
    radio_state.remove("console.html")
    page.goto(base + "/")
    expect(_live_frame(page).locator(".rc-off")).to_have_text("station offline")
    expect(page.locator("section.console audio.console-audio")).to_have_count(1)
    expect(page.locator("iframe.shell-frame.cur")).to_be_visible()
