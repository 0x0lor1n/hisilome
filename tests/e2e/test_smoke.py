"""Both engines open the shell. Everything else builds on this."""


def test_shell_loads(page, base):
    page.goto(base + "/")
    assert "Hísilómë" in page.title()
    assert page.locator("iframe.cur").count() == 1
