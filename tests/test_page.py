from pyseoanalyzer import page


def test_page_init():
    p = page.Page(
        url="https://www.sethserver.com/sitemap.xml",
        base_domain="https://www.sethserver.com/",
    )

    assert p.base_domain.scheme == "https"
    assert p.base_domain.netloc == "www.sethserver.com"
    assert p.base_domain.path == "/"

    assert p.url == "https://www.sethserver.com/sitemap.xml"

    assert p.title == ""
    assert p.description == ""
    assert p.keywords == {}
    assert p.warnings == []
    assert p.links == []


def test_analyze():
    p = page.Page(
        url="https://www.sethserver.com/", base_domain="https://www.sethserver.com/"
    )

    assert p.analyze()

    assert "seth" in p.title.lower()


def test_analyze_html_lang_missing():
    from bs4 import BeautifulSoup

    p = page.Page(url="https://example.com/", base_domain="https://example.com/")
    soup = BeautifulSoup(
        "<html><head><title>Test</title></head><body><p>Hello</p></body></html>",
        "html.parser",
    )
    p.analyze_html_lang(soup)
    assert len(p.warnings) == 1
    assert "lang" in p.warnings[0].lower()


def test_analyze_html_lang_present():
    from bs4 import BeautifulSoup

    p = page.Page(url="https://example.com/", base_domain="https://example.com/")
    soup = BeautifulSoup(
        '<html lang="en"><head><title>Test</title></head><body><p>Hello</p></body></html>',
        "html.parser",
    )
    p.analyze_html_lang(soup)
    assert len(p.warnings) == 0


def test_analyze_with_llm():
    p = page.Page(
        url="https://www.sethserver.com/",
        base_domain="https://www.sethserver.com/",
        run_llm_analysis=True,
    )

    assert p.analyze()

    assert "seth" in p.title.lower()
    assert "summary" in p.llm_analysis
