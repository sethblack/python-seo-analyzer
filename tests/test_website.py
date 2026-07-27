from pyseoanalyzer.website import Website


def test_check_ai_crawler_access_allows_and_has_llms_txt():
    site = Website(
        base_url="https://alexander-k-eliot.github.io/ai-visibility-check-free/",
        sitemap=None,
    )

    result = site.check_ai_crawler_access()

    assert result["robots_txt_found"] is True
    assert result["llms_txt"] is True
    assert result["blocked_ai_bots"] == []
    assert result["blocked_training_bots"] == []
    assert result["blocked_retrieval_bots"] == []


def test_check_ai_crawler_access_detects_blocked_bots():
    site = Website(
        base_url="https://wilreynolds.com/",
        sitemap=None,
    )

    result = site.check_ai_crawler_access()

    assert result["robots_txt_found"] is True
    assert "GPTBot" in result["blocked_ai_bots"]
    assert "ClaudeBot" in result["blocked_ai_bots"]


def test_check_ai_crawler_access_separates_training_and_retrieval():
    # wilreynolds.com blocks all 4 training crawlers (GPTBot, Google-Extended,
    # ClaudeBot, anthropic-ai) plus one retrieval crawler (PerplexityBot), but
    # allows OAI-SearchBot/ChatGPT-User/Claude-User -- a real, live example of
    # exactly the mixed case the split is meant to surface.
    site = Website(
        base_url="https://wilreynolds.com/",
        sitemap=None,
    )

    result = site.check_ai_crawler_access()

    assert set(result["blocked_training_bots"]) == {
        "GPTBot",
        "Google-Extended",
        "ClaudeBot",
        "anthropic-ai",
    }
    assert result["blocked_retrieval_bots"] == ["PerplexityBot"]
    # every blocked bot must land in exactly one category, and the union
    # must equal the unchanged, backward-compatible blocked_ai_bots list
    assert set(result["blocked_training_bots"]) | set(
        result["blocked_retrieval_bots"]
    ) == set(result["blocked_ai_bots"])
    assert set(result["blocked_training_bots"]).isdisjoint(
        result["blocked_retrieval_bots"]
    )


def test_website_init_sets_default_ai_crawler_access():
    site = Website(
        base_url="https://example.com/",
        sitemap=None,
    )

    assert site.ai_crawler_access == {
        "llms_txt": False,
        "robots_txt_found": False,
        "blocked_ai_bots": [],
        "blocked_training_bots": [],
        "blocked_retrieval_bots": [],
    }
