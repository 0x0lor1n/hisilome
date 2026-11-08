"""Browser tests for the shell, run against the dev stack (`nix run .#e2e`).

The suite observes; it never edits templates or nginx config. What it may
touch is `radio/state/` -- the fragments nginx includes by SSI -- and only
through the `radio_state` fixture, which puts every file back on teardown.

Every test runs once per engine: `browser_name` is parametrised over Chromium
and Firefox. Firefox needs the `pw-firefox` wrapper from nix/packages.nix
(`PLAYWRIGHT_FIREFOX_EXECUTABLE`); without it the launch times out on hosts
with a dump()-silencing autoconfig.
"""

import ipaddress
import json
import os
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import Page, sync_playwright

REPO = Path(__file__).resolve().parents[2]
STATE_DIR = REPO / "radio" / "state"
FIXTURES = Path(__file__).parent / "state"

# The fragments the radio side writes and nginx includes (nix/packages.nix
# `fragments`). The fixture snapshots exactly these, nothing else in radio/state/.
FRAGMENTS = (
    "console.html",
    "refresh.html",
    "schedule.html",
    "listeners.txt",
    "now-playing.txt",
    "status.html",
)

ENGINES = ("chromium", "firefox")

# process-compose processes that rewrite the fragments (console.html every
# second). They are stopped for the session the first time a test writes a
# fragment and started again at the end; otherwise a fixture is overwritten
# before the page loads.
WRITERS = ("liquidsoap", "listeners")


def pytest_addoption(parser):
    parser.addoption(
        "--engine",
        action="append",
        choices=ENGINES,
        help="run only this engine (repeatable); default: all",
    )


def pytest_generate_tests(metafunc):
    if "browser_name" in metafunc.fixturenames:
        engines = metafunc.config.getoption("--engine") or ENGINES
        metafunc.parametrize("browser_name", engines, scope="session")


@pytest.fixture(scope="session")
def base() -> str:
    """Base URL; loopback only, so a misconfigured env can never hit hisilo.me."""
    url = os.environ.get("E2E_BASE", "http://127.0.0.1:8099").rstrip("/")
    host = urlsplit(url).hostname or ""
    try:
        loopback = ipaddress.ip_address(host).is_loopback
    except ValueError:
        loopback = host == "localhost"
    if not loopback:
        pytest.exit(f"E2E_BASE must be loopback, got {url}", returncode=2)
    return url


@pytest.fixture(scope="session")
def playwright():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright, browser_name):
    kwargs: dict = {"headless": True}
    if browser_name == "firefox":
        exe = os.environ.get("PLAYWRIGHT_FIREFOX_EXECUTABLE")
        if exe:
            kwargs["executable_path"] = exe
    b = getattr(playwright, browser_name).launch(**kwargs)
    yield b
    b.close()


# nginx: `limit_req zone=pages rate=10r/s burst=40` per client address. The
# whole suite is one address, a shell load is ~10 requests, so back-to-back
# tests drain the bucket and a 429 on style.css renders a page unstyled -- a
# flake, not a finding. Pause between pages so the bucket refills, and turn
# any 429 the browser did see into an explicit failure.
PACE_SECONDS = 1.0


@pytest.fixture
def page(browser) -> Page:
    time.sleep(PACE_SECONDS)
    ctx = browser.new_context()
    pg = ctx.new_page()
    limited: list[str] = []
    pg.on(
        "response",
        lambda r: limited.append(r.url) if r.status == 429 else None,
    )
    yield pg
    ctx.close()
    assert not limited, f"nginx rate limit hit, suite needs pacing: {limited}"


class ProcessCompose:
    """The dev stack's process-compose REST API (`process-compose up -p N`)."""

    def __init__(self, url: str):
        self.url = url.rstrip("/")

    def _call(self, method: str, path: str):
        req = urllib.request.Request(self.url + path, method=method)
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.load(r)

    def reachable(self) -> bool:
        try:
            self._call("GET", "/processes")
            return True
        except (urllib.error.URLError, OSError, ValueError):
            return False

    def status(self, name: str) -> str:
        return self._call("GET", f"/process/{name}")["status"]

    def stop(self, name: str):
        if self.status(name) == "Running":
            self._call("PATCH", f"/process/stop/{name}")

    def start(self, name: str):
        if self.status(name) != "Running":
            self._call("POST", f"/process/start/{name}")


@pytest.fixture(scope="session")
def paused_writers():
    """Stop the fragment writers for the rest of the session; restart at the end.

    Skips the requesting test when the process-compose API is not reachable
    (E2E_PC, default :8081): then nothing can hold the writers still and a
    fragment test would race liquidsoap.
    """
    pc = ProcessCompose(os.environ.get("E2E_PC", "http://127.0.0.1:8081"))
    if not pc.reachable():
        pytest.skip(f"process-compose API not reachable at {pc.url}; set E2E_PC")
    for name in WRITERS:
        pc.stop(name)
    # SIGTERM goes to the `station-online; liquidsoap; station-offline` shell,
    # so neither station-* runs; give the files a moment to settle anyway.
    time.sleep(0.5)
    yield pc
    for name in WRITERS:
        pc.start(name)


class RadioState:
    """Write SSI fragments under radio/state/; the fixture restores them."""

    def __init__(self):
        self._saved = {}
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        for name in FRAGMENTS:
            p = STATE_DIR / name
            self._saved[name] = p.read_bytes() if p.exists() else None

    def write(self, name: str, content: str | bytes):
        if name not in FRAGMENTS:
            raise ValueError(f"{name} is not an SSI fragment")
        data = content.encode() if isinstance(content, str) else content
        # The writers on the radio side go through rename too: nginx must
        # never read a half-written fragment.
        tmp = STATE_DIR / f"{name}.e2e-tmp"
        tmp.write_bytes(data)
        tmp.replace(STATE_DIR / name)

    def fixture(self, name: str, fixture_file: str | None = None):
        self.write(name, (FIXTURES / (fixture_file or name)).read_bytes())

    def remove(self, name: str):
        if name not in FRAGMENTS:
            raise ValueError(f"{name} is not an SSI fragment")
        (STATE_DIR / name).unlink(missing_ok=True)

    def restore(self):
        for name, data in self._saved.items():
            p = STATE_DIR / name
            if data is None:
                p.unlink(missing_ok=True)
            else:
                self.write(name, data)


@pytest.fixture
def radio_state(paused_writers):
    st = RadioState()
    yield st
    st.restore()


class NavToken:
    """Detects a full document load: `window.__t` survives a hash change only."""

    def __init__(self, page: Page):
        self.page = page
        self.value = str(uuid.uuid4())

    def set(self):
        self.page.evaluate("t => { window.__t = t }", self.value)
        return self

    def kept(self) -> bool:
        return self.page.evaluate("() => window.__t") == self.value


@pytest.fixture
def nav_token(page):
    return NavToken(page)


class Console:
    """The shell's radio console: one <audio>, fold checkbox, live frame."""

    def __init__(self, page: Page):
        self.page = page
        self.audio = page.locator("audio.console-audio")
        self.fold = page.locator("#console-fold")
        self.chevron = page.locator("label.console-chevron")

    def state(self) -> dict:
        return self.audio.evaluate(
            "a => ({paused: a.paused, time: a.currentTime,"
            " src: a.currentSrc, error: a.error && a.error.code})"
        )

    def play(self):
        """Start playback as a script would after a user gesture.

        The native controls' play button has no stable hit box across engines
        (Chromium 54 px tall, Firefox 40), so play() is called directly; the
        test still checks that the element plays, which is what matters.
        """
        self.audio.evaluate("a => a.play()")

    def wait_advancing(self, seconds: float = 1.0):
        """currentTime moved forward by at least `seconds` -- real decoding, not
        just `paused == false`, which Firefox reports even with no audio sink."""
        t0 = self.state()["time"]
        self.page.wait_for_function(
            "([a, t]) => !a.paused && a.currentTime >= t",
            arg=[self.audio.element_handle(), t0 + seconds],
            timeout=10_000,
        )


@pytest.fixture
def tone(page) -> Path:
    """Serve 30 s of Opus as /stream.opus in this page, not icecast's stream.

    Icecast's live stream is infinite and may be absent (liquidsoap stopped by
    `paused_writers`); the console tests only need an <audio> that decodes.
    The file comes from the e2e env (E2E_TONE, built in nix/packages.nix).
    """
    path = Path(os.environ.get("E2E_TONE", ""))
    if not path.name or not path.exists():
        pytest.skip("E2E_TONE not set; run through `nix run .#e2e` or the e2e shell")
    body = path.read_bytes()
    page.route(
        "**/stream.opus",
        lambda route: route.fulfill(status=200, content_type="audio/ogg", body=body),
    )
    return path


@pytest.fixture
def console(page) -> Console:
    return Console(page)
