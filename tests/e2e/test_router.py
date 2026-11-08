"""The CSS router in templates/listen.html and the nginx maps behind it.

Every page URL serves the shell; the page itself is the last frame (`.cur`).
Topbar links set the fragment, `:target` shows that route's frame, and
nothing reloads, so `<audio>` in the shell keeps playing.
"""

from urllib.parse import urlsplit

import pytest
from playwright.sync_api import Page, expect

ENTRY_URLS = ("/", "/logs/", "/colophon/")
DOC = {"Sec-Fetch-Dest": "document"}


def frame(page: Page, route: str):
    return page.locator(f'iframe.shell-frame[id="{route}"]')


def cur(page: Page):
    return page.locator("iframe.shell-frame.cur")


def a_post(page: Page, base: str) -> str:
    """Path of one post linked from /logs/, read from the page, not hardcoded."""
    html = page.request.get(base + "/logs/").text()
    start = html.index('class="post-title" href="') + len('class="post-title" href="')
    return html[start : html.index('"', start)]


def route_ids(page: Page) -> list[str]:
    return page.locator("iframe.shell-frame[id]").evaluate_all(
        "fs => fs.map(f => f.id)"
    )


def loaded_routes(page: Page) -> set[str]:
    """Route frames whose document left about:blank, i.e. that were fetched.

    Chromium leaves lazy iframe loads out of page.on("request"), so the frame
    documents are the evidence, not the request log.
    """
    return set(
        page.locator("iframe.shell-frame[id]").evaluate_all(
            "fs => fs.filter(f => f.contentDocument"
            " && f.contentDocument.URL !== 'about:blank').map(f => f.id)"
        )
    )


@pytest.mark.parametrize("entry", ENTRY_URLS)
def test_entry_serves_shell(page, base, entry):
    page.goto(base + entry)
    expect(page.locator("body.shell-body")).to_have_count(1)
    expect(cur(page)).to_have_attribute("src", entry)
    expect(cur(page)).to_be_visible()
    assert entry not in route_ids(page)


def test_post_entry_serves_shell(page, base):
    post = a_post(page, base)
    page.goto(base + post)
    expect(page.locator("body.shell-body")).to_have_count(1)
    expect(cur(page)).to_have_attribute("src", post)
    assert post not in route_ids(page)


def test_listen_redirects_to_root(page, base):
    r = page.request.get(base + "/listen/", max_redirects=0)
    assert r.status == 301
    assert urlsplit(r.headers["location"]).path == "/"


def test_topbar_click_targets_frame(page, base, nav_token):
    page.goto(base + "/")
    nav_token.set()
    page.locator('a.ls-row[href="#/logs/"]').click()
    expect(page).to_have_url(base + "/#/logs/")
    expect(frame(page, "/logs/")).to_be_visible()
    expect(cur(page)).to_be_hidden()
    assert nav_token.kept()


def test_hidden_frames_not_fetched(page, base):
    page.goto(base + "/")
    page.wait_for_load_state("networkidle")
    assert loaded_routes(page) == set()

    page.locator('a.ls-row[href="#/colophon/"]').click()
    colophon = frame(page, "/colophon/").element_handle().content_frame()
    colophon.wait_for_url(base + "/colophon/")
    page.wait_for_load_state("networkidle")
    assert loaded_routes(page) == {"/colophon/"}


def test_link_inside_frame_targets_post(page, base, nav_token):
    post = a_post(page, base)
    page.goto(base + "/#/logs/")
    nav_token.set()
    logs = page.frame_locator('iframe.shell-frame[id="/logs/"]')
    link = logs.locator(f'a.post-title[href$="#{post}"]')
    expect(link).to_have_attribute("target", "_top")
    link.click()
    expect(page).to_have_url(f"{base}/#{post}")
    expect(frame(page, post)).to_be_visible()
    expect(frame(page, "/logs/")).to_be_hidden()
    assert nav_token.kept()


def test_frame_hrefs_follow_referer(page, base):
    post = a_post(page, base)
    plain = page.request.get(base + "/logs/").text()
    assert f'href="{post}"' in plain
    assert 'target="_top"' not in plain

    framed = page.request.get(
        base + "/logs/",
        headers={"Sec-Fetch-Dest": "iframe", "Referer": base + "/"},
    ).text()
    assert f'href="{base}/#{post}" target="_top"' in framed

    # A query string in the Referer is not a shell URL: plain links.
    queried = page.request.get(
        base + "/logs/",
        headers={"Sec-Fetch-Dest": "iframe", "Referer": base + "/?x=1"},
    ).text()
    assert f'href="{post}"' in queried


def test_back_forward_restores_target(page, base):
    page.goto(base + "/")
    page.locator('a.ls-row[href="#/logs/"]').click()
    expect(frame(page, "/logs/")).to_be_visible()
    page.locator('a.ls-row[href="#/colophon/"]').click()
    expect(frame(page, "/colophon/")).to_be_visible()

    page.go_back()
    expect(page).to_have_url(base + "/#/logs/")
    expect(frame(page, "/logs/")).to_be_visible()
    expect(frame(page, "/colophon/")).to_be_hidden()

    page.go_back()
    expect(page).to_have_url(base + "/")
    expect(cur(page)).to_be_visible()
    expect(frame(page, "/logs/")).to_be_hidden()

    page.go_forward()
    expect(frame(page, "/logs/")).to_be_visible()
    expect(cur(page)).to_be_hidden()


def test_deep_link(page, base):
    page.goto(base + "/logs/#/colophon/")
    expect(cur(page)).to_have_attribute("src", "/logs/")
    expect(frame(page, "/colophon/")).to_be_visible()
    expect(cur(page)).to_be_hidden()


def test_body_class_by_fetch_dest(page, base):
    plain = page.request.get(base + "/logs/").text()
    assert "<body>" in plain
    assert "shell-body" not in plain

    framed = page.request.get(base + "/logs/", headers={"Sec-Fetch-Dest": "iframe"})
    assert '<body class="framed">' in framed.text()

    shell = page.request.get(base + "/logs/", headers=DOC)
    assert '<body class="shell-body">' in shell.text()


@pytest.mark.parametrize("query", ["", "?x=1"])
def test_shell_carries_page_meta(page, base, query):
    post = a_post(page, base)
    own = page.request.get(base + post + "meta.html").text()
    title = own[own.index("<title>") + 7 : own.index("</title>")]
    page.goto(base + post + query)
    assert page.title() == title
    og = page.locator('meta[property="og:title"]')
    expect(og).to_have_count(1)
    assert og.get_attribute("content") in title


@pytest.mark.parametrize("entry", ["/", "/logs/", "post"])
@pytest.mark.parametrize("query", ["", "?x=1"])
def test_shell_canonical_is_the_wrapped_page(page, base, entry, query):
    """A deep entry (/<post>/) is a sticky door: every later hash route hangs
    off it. The canonical must point search engines and copy-pasters at the
    page itself, never at /listen/ (a 301) and never with the query."""
    path = a_post(page, base) if entry == "post" else entry
    plain = page.request.get(base + path).text()
    own = plain[plain.index('rel="canonical" href="') + 22 :]
    own = own[: own.index('"')]
    assert own.endswith(path)

    shell = page.request.get(base + path + query, headers=DOC).text()
    assert shell.count('rel="canonical"') == 1
    assert f'rel="canonical" href="{own}"' in shell
    assert "/listen/" not in shell.split("<body", 1)[0]


def test_unknown_url_404_inside_frame(page, base):
    # The shell itself answers 200: try_files picks the shell for any document path.
    r = page.goto(base + "/nope/")
    assert r.status == 200
    assert page.title().endswith(" - radio")
    expect(page.locator("header.topbar")).to_be_visible()
    inner = cur(page).element_handle().content_frame()
    inner.wait_for_load_state()
    assert inner.title() == "404 - Hísilómë"

    plain = page.request.get(base + "/nope/")
    assert plain.status == 404
    assert "shell-body" not in plain.text()


@pytest.mark.parametrize("entry", ["/", "/logs/"])
def test_narrow_viewport_no_overflow(page, base, entry):
    page.set_viewport_size({"width": 375, "height": 812})
    page.goto(base + entry)
    page.wait_for_load_state("networkidle")
    overflow = "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
    assert page.evaluate(overflow) == 0
    inner = cur(page).element_handle().content_frame()
    inner.wait_for_load_state()
    assert inner.evaluate(overflow) == 0


def test_narrow_ls_targets_ls_frame(page, base, nav_token):
    page.set_viewport_size({"width": 375, "height": 812})
    page.goto(base + "/")
    nav_token.set()
    page.locator("a.ls-cmd").click()
    expect(page).to_have_url(base + "/#/ls/")
    expect(frame(page, "/ls/")).to_be_visible()
    expect(cur(page)).to_be_hidden()
    assert nav_token.kept()
