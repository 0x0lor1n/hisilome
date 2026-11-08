"""What nginx promises over plain HTTP, checked without a browser.

Headers and bodies the shell's design leans on: fragments uncached and never
SSI-processed (a title liquidsoap writes must not become a directive),
versioned assets immutable, the feed's `<!--#echo` resolved, the stream proxied
with `Icy-MetaData` stripped, and the per-address rate limit. One `urllib`
client per request -- the paced `page` fixture is deliberately not used here,
the point of the burst test is to drain the bucket.

The dev conf (nix/packages.nix `devNginxConf`) renders `nginxLocations` with
`extraHeaders = ""`; the security headers only exist in the NixOS module. What
can be pinned here is the inheritance rule: every location that sets its own
`add_header` must also splice `${extraHeaders}`, or the module's CSP silently
disappears on that path.
"""

import re
import socket
import time
import urllib.error
import urllib.request

import pytest
from conftest import REPO

PACKAGES_NIX = (REPO / "nix" / "packages.nix").read_text()
NGINX_MODULE = (REPO / "nix" / "modules" / "nginx.nix").read_text()

# nginx `limit_req zone=pages rate=10r/s burst=40` (nginxHttpConfig/pageLimit).
RATE, BURST = 10, 40


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def _get(url: str, headers: dict | None = None, method: str = "GET"):
    """One request, no redirects followed, 4xx/5xx returned instead of raised."""
    req = urllib.request.Request(url, headers=headers or {}, method=method)
    try:
        return _OPENER.open(req, timeout=10)
    except urllib.error.HTTPError as e:
        return e


def _fragments() -> list[tuple[str, str, str]]:
    """(url name, state file, mime type) from the `fragments` list in packages.nix."""
    block = re.search(r"fragments = \[(.*?)\n  \];", PACKAGES_NIX, re.DOTALL).group(1)
    found = re.findall(
        r'name = "([^"]+)";\s*file = "([^"]+)";\s*type = "([^"]+)";', block
    )
    assert len(found) >= 5, "fragments list not parsed from nix/packages.nix"
    return found


def _dev_origin() -> str:
    return re.search(r'set \$hisilome_origin "([^"]+)";', PACKAGES_NIX).group(1)


@pytest.mark.parametrize("name,_file,mime", _fragments())
def test_fragment_uncached_and_typed(base, name, _file, mime):
    """Each fragment is `no-store` with the type the nix list declares.

    Absent fragments (schedule-body.html when liquidsoap has not written one
    yet) are a 404, and that is fine: the shell's include has a stub for it.
    """
    r = _get(f"{base}/{name}")
    if r.status == 404:
        pytest.skip(f"/{name} not written by the radio side right now")
    assert r.status == 200
    assert r.headers.get("Content-Type", "").split(";")[0] == mime
    assert "no-store" in r.headers.get("Cache-Control", "")


def test_fragment_served_verbatim_and_inert_when_included(base, radio_state):
    """`ssi off` on the fragment location, and the shell does not re-run SSI on
    what it included: a directive inside console.html stays literal both ways.

    Liquidsoap writes track titles into the fragment; a title that looks like
    `<!--#exec` must never reach nginx's SSI parser.
    """
    body = '<p class="rc-title">E2E <!--#echo var="hisilome_origin" default="X" --></p>'
    radio_state.write("console.html", body)
    raw = _get(base + "/console.html")
    assert raw.status == 200
    assert raw.read().decode() == body

    live = _get(base + "/live.html").read().decode()
    assert body in live, "the include was SSI-processed or not spliced"


def test_style_and_fonts_immutable(base):
    """Cache-busted by `?v=` and by file name, so a year is safe."""
    font = next((REPO / "public" / "fonts").glob("*.woff2")).name
    for path in ("/style.css", f"/fonts/{font}"):
        r = _get(base + path)
        assert r.status == 200, path
        cc = r.headers.get("Cache-Control", "")
        assert "immutable" in cc and "max-age=31536000" in cc, (path, cc)


def test_listen_redirects_to_root(base):
    """The shell template is rendered at /listen/ only so zola builds it."""
    r = _get(base + "/listen/")
    assert r.status == 301
    assert r.headers["Location"].rstrip("/") == base


def test_every_add_header_location_splices_extra_headers():
    """nginx: `add_header` in a location discards the inherited set.

    Any location in `nginxLocations` that adds its own header must repeat
    `${extraHeaders}`; otherwise the module's CSP/HSTS vanish on that path and
    nothing in the dev stack would show it. Pins the comment above
    `nginxLocations`, in code.
    """
    block = re.search(
        r"nginxLocations = \{(.*?)\n  # Relative paths", PACKAGES_NIX, re.DOTALL
    )
    assert block, "nginxLocations block not found"
    bodies = re.findall(r"extraConfig = ''(.*?)'';", block.group(1), re.DOTALL)
    assert len(bodies) >= 5
    for body in bodies:
        if "add_header" in body:
            assert "${extraHeaders}" in body, body.strip()


def test_module_passes_headers_to_every_vhost():
    """Both vhost kinds hand their header set to nginxLocations."""
    calls = re.findall(r"nginxLocations \{(.*?)\};", NGINX_MODULE, re.DOTALL)
    assert len(calls) == 2, "expected the clearnet and the overlay vhost"
    assert all("extraHeaders = " in c for c in calls)
    # Overlay hosts keep the redirect host-relative (onion port mapping).
    assert "absolute_redirect off;" in NGINX_MODULE


def test_security_headers_survive_own_add_header(base):
    """Runtime side of the inheritance rule, when the conf under test has them.

    Dev renders with `extraHeaders = ""`, so this skips there; against a
    module-rendered conf (E2E_BASE at a prod-like port) it checks that the CSP
    the root page carries is also on the paths that set Cache-Control.
    """
    root = _get(base + "/")
    csp = root.headers.get("Content-Security-Policy")
    if not csp:
        pytest.skip('no security headers in this conf (dev: extraHeaders = "")')
    for path in ("/style.css", "/console.html", "/listeners.txt"):
        r = _get(base + path)
        assert r.headers.get("Content-Security-Policy") == csp, path
        assert r.headers.get("X-Content-Type-Options") == "nosniff", path


def test_overlay_relative_redirect(base):
    """An overlay vhost must not name the loopback port in Location.

    There is no overlay listener in the dev conf; the rule is pinned
    statically in test_module_passes_headers_to_every_vhost.
    """
    pytest.skip("no overlay vhost in the dev conf")


def test_rss_echo_resolved(base):
    """`ssi_types text/xml` -- the feed's `<!--#echo var="hisilome_origin"` is
    resolved to this server's origin, not shipped raw and not the default."""
    r = _get(base + "/rss.xml")
    assert r.status == 200
    assert r.headers.get("Content-Type", "").startswith("text/xml")
    body = r.read().decode()
    assert "<!--#" not in body
    assert _dev_origin() in body


def _mount_live() -> bool:
    """Icecast on :8000 with a source on /stream.opus.

    Raw socket: Icecast answers `ICY 200 OK` to this header, which urllib
    rejects as a bad status line. The mount is 404 whenever no source is
    connected.
    """
    try:
        with socket.create_connection(("127.0.0.1", 8000), timeout=1) as s:
            s.sendall(b"GET /stream.opus HTTP/1.0\r\nHost: x\r\n\r\n")
            return b" 200 " in s.recv(64)
    except OSError:
        return False


@pytest.fixture
def live_mount(paused_writers):
    """A source on /stream.opus for one test.

    `paused_writers` stops liquidsoap for the session (fragment tests must not
    race it), so in a full run the mount is 404 by the time this module runs.
    Start it back up, wait for the mount, stop it again after: the session
    fixture's end-of-run start is unaffected.
    """
    pc = paused_writers
    if _mount_live():
        yield
        return
    pc.start("liquidsoap")
    deadline = time.monotonic() + 20
    while not _mount_live():
        if time.monotonic() > deadline:
            pc.stop("liquidsoap")
            pytest.skip("liquidsoap started but /stream.opus did not come up in 20 s")
        time.sleep(0.5)
    yield
    pc.stop("liquidsoap")


def test_stream_proxied_with_icy_header_stripped(base, live_mount):
    """A client asking for `Icy-MetaData: 1` still gets a plain `HTTP/1.1 200`
    Ogg stream: nginx blanks the header, else Icecast answers `ICY 200 OK` and
    nginx turns that into a 502.

    Icecast refuses HEAD (405, `Allow: GET, DELETE, OPTIONS`), so this reads
    the first bytes of a GET and closes.
    """
    r = _get(base + "/stream.opus", {"Icy-MetaData": "1"})
    try:
        assert r.status == 200
        assert r.headers.get("Content-Type", "").startswith("audio/ogg")
        assert r.read(4) == b"OggS"
    finally:
        r.close()


# Last in the module: it drains the per-address bucket on purpose.
def test_page_burst_is_limited(base):
    """`limit_req zone=pages rate=10r/s burst=40 nodelay`: a back-to-back
    burst passes burst+1 and the rest are 429, not queued (nodelay)."""
    # Let the bucket refill from whatever ran before.
    time.sleep(BURST / RATE + 1)
    codes = []
    t0 = time.monotonic()
    for _ in range(BURST + 30):
        r = _get(base + "/404.html")
        codes.append(r.status)
        r.close()
    elapsed = time.monotonic() - t0
    # Loopback does 70 requests in well under a second; if that ever stalls
    # the token arithmetic below is void, so say so instead of mis-reporting.
    assert elapsed < 2, f"burst took {elapsed:.1f}s; nodelay would be queueing"
    assert 429 in codes, codes
    first = codes.index(429)
    # Exactly the bucket passes, plus the tokens a sub-second loop earns back.
    assert BURST + 1 <= first <= BURST + 1 + int(elapsed * RATE) + 1, (first, elapsed)
    assert set(codes[first:]) == {429}, codes[first:]
    # Leave a full bucket for the next module's page loads.
    time.sleep(BURST / RATE + 1)
