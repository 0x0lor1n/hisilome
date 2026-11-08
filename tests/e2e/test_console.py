"""The radio console in the shell (templates/macros.html `shell_console`).

The whole point of the shell is that the one <audio> lives outside the route
frames, so it keeps playing across navigation and across the fold. The fold
is a checkbox, not <details>, because closing a <details> drops the element
and with it the playback (comment in the macro). These tests pin both.

/stream.opus is answered from a fixture file (`tone`); icecast is not needed.
"""

import pytest
from playwright.sync_api import expect

ROUTE = 'a.ls-row[href="#/logs/"]'


def test_one_audio_in_shell_none_in_frames(page, base):
    page.goto(base + "/")
    expect(page.locator("audio")).to_have_count(1)
    expect(page.locator("section.console audio.console-audio")).to_have_count(1)
    # Route frames (and the console's own live/schedule frames) carry none:
    # a second player would steal the stream on navigation.
    in_frames = page.evaluate(
        "() => [...document.querySelectorAll('iframe')]"
        "  .map(f => f.contentDocument"
        "    ? f.contentDocument.querySelectorAll('audio').length : 0)"
        "  .reduce((a, b) => a + b, 0)"
    )
    assert in_frames == 0


def test_plays_and_keeps_playing_across_route(page, base, tone, console, nav_token):
    page.goto(base + "/")
    nav_token.set()
    console.play()
    console.wait_advancing()
    st = console.state()
    assert st["src"].endswith("/stream.opus"), st
    assert st["error"] is None, st

    page.locator(ROUTE).click()
    expect(page.locator('iframe.shell-frame[id="/logs/"]')).to_be_visible()
    assert nav_token.kept()
    console.wait_advancing()
    assert not console.state()["paused"]


def test_fold_hides_controls_and_keeps_audio(page, base, tone, console):
    page.goto(base + "/")
    console.play()
    console.wait_advancing()
    play, meta = page.locator(".console-play"), page.locator(".console-meta")
    expect(play).to_be_visible()
    expect(meta).to_be_visible()

    # The input is visually hidden (1 px, opacity 0); the label is the control.
    console.chevron.click()
    expect(console.fold).to_be_checked()
    expect(play).to_be_hidden()
    expect(meta).to_be_hidden()
    # display:none, not removed: the element and its playback survive.
    expect(console.audio).to_have_count(1)
    console.wait_advancing()

    console.chevron.click()
    expect(console.fold).not_to_be_checked()
    expect(play).to_be_visible()
    expect(meta).to_be_visible()
    assert not console.state()["paused"]


def test_fold_survives_route_change(page, base, tone, console):
    page.goto(base + "/")
    console.chevron.click()
    expect(console.fold).to_be_checked()
    page.locator(ROUTE).click()
    expect(page.locator('iframe.shell-frame[id="/logs/"]')).to_be_visible()
    expect(console.fold).to_be_checked()
    expect(page.locator(".console-play")).to_be_hidden()


@pytest.mark.parametrize("entry", ("/", "/logs/", "/colophon/"))
def test_console_present_on_every_entry(page, base, entry):
    """Each entry URL serves its own shell; the console must be in all of them,
    or a deep link would land on a page without a player."""
    page.goto(base + entry)
    expect(page.locator("section.console audio.console-audio")).to_have_count(1)
    expect(page.locator("iframe.console-live")).to_have_attribute("src", "/live.html")
