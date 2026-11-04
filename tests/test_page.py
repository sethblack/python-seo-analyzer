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


def _structured_data_page(head):
    from bs4 import BeautifulSoup

    p = page.Page(url="https://example.com/", base_domain="https://example.com/")
    soup = BeautifulSoup(
        f"<html><head>{head}</head><body><p>Hello</p></body></html>", "html.parser"
    )
    p.analyze_structured_data(soup)
    return p


def test_analyze_structured_data_missing():
    p = _structured_data_page("<title>Test</title>")
    assert p.structured_data == []
    assert len(p.warnings) == 1
    assert "json-ld" in p.warnings[0].lower()


def test_analyze_structured_data_types():
    p = _structured_data_page(
        '<script type="application/ld+json">'
        '{"@context": "https://schema.org", "@type": "Organization", "name": "Example"}'
        "</script>"
        '<script type="application/ld+json">'
        '{"@context": "https://schema.org", "@graph": ['
        '{"@type": "WebSite"}, {"@type": ["Article", "NewsArticle"]},'
        ' {"@type": "Organization"}]}'
        "</script>"
    )
    assert p.warnings == []
    assert p.structured_data == ["Organization", "WebSite", "Article", "NewsArticle"]


def test_analyze_structured_data_invalid_json():
    p = _structured_data_page(
        '<script type="application/ld+json">{"@type": "Product",}</script>'
    )
    assert p.structured_data == []
    assert len(p.warnings) == 1
    assert p.warnings[0].startswith("Invalid JSON-LD structured data")


def test_analyze_reports_structured_data():
    text = " ".join(["Structured data helps search engines read this page."] * 20)
    html = (
        '<html lang="en"><head><title>Structured data test page</title>'
        '<script type="application/ld+json">[{"@type": "FAQPage"}]</script>'
        f"</head><body><h1>Test</h1><p>{text}</p></body></html>"
    )
    p = page.Page(url="https://example.com/", base_domain="https://example.com/")
    assert p.analyze(raw_html=html)
    assert p.as_dict()["structured_data"] == ["FAQPage"]
    assert not any("JSON-LD" in w for w in p.warnings)


def test_analyze_with_llm():
    p = page.Page(
        url="https://www.sethserver.com/",
        base_domain="https://www.sethserver.com/",
        run_llm_analysis=True,
    )

    assert p.analyze()

    assert "seth" in p.title.lower()
    assert "summary" in p.llm_analysis
