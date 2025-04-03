import time
import pytest
from unittest.mock import patch, MagicMock
from pyseoanalyzer.analyzer import analyze, calc_total_time


# --- Test calc_total_time ---


def test_calc_total_time():
    start_time = time.time()
    # Simulate some time passing
    time.sleep(0.01)
    elapsed_time = calc_total_time(start_time)
    # Check if the elapsed time is roughly correct (allow for some variance)
    assert 0.005 < elapsed_time < 0.05


# --- Test analyze function ---


# Helper function to create a mock Page object
def create_mock_page(url, title, description, word_count, content_hash):
    page = MagicMock()
    page.url = url
    page.content_hash = content_hash
    page.as_dict.return_value = {
        "url": url,
        "title": title,
        "description": description,
        "word_count": word_count,
        # Add other fields as needed by as_dict() if tests evolve
    }
    return page


# Basic test using mocking
@patch("pyseoanalyzer.analyzer.Website")
def test_analyze_basic(MockWebsite):
    # --- Setup Mock ---
    mock_site_instance = MockWebsite.return_value
    mock_page1 = create_mock_page(
        "http://example.com", "Page 1", "Desc 1", 100, "hash1"
    )
    mock_site_instance.crawled_pages = [mock_page1]
    mock_site_instance.content_hashes = {"hash1": ["http://example.com"]}
    mock_site_instance.wordcount = {"word": 5, "test": 6}
    mock_site_instance.bigrams = {("bigram", "test"): 5}
    mock_site_instance.trigrams = {("trigram", "test", "word"): 5}

    # --- Run analyze ---
    output = analyze("http://example.com", follow_links=False)

    # --- Assertions ---
    # Check Website constructor call
    MockWebsite.assert_called_once_with(
        base_url="http://example.com",
        sitemap=None,
        analyze_headings=False,
        analyze_extra_tags=False,
        follow_links=False,
        run_llm_analysis=False,
    )
    # Check crawl was called
    mock_site_instance.crawl.assert_called_once()

    # Check output structure and basic content
    assert len(output["pages"]) == 1
    assert output["pages"][0]["url"] == "http://example.com"
    assert output["pages"][0]["title"] == "Page 1"
    assert output["pages"][0]["description"] == "Desc 1"
    assert output["pages"][0]["word_count"] == 100
    # assert output["errors"] == [] # Errors usually come from crawl, harder to test here
    assert output["duplicate_pages"] == []  # Only one page

    # Check keywords (counts > 4)
    assert len(output["keywords"]) == 4
    assert {"word": "test", "count": 6} in output["keywords"]
    assert {"word": "word", "count": 5} in output["keywords"]
    assert {"word": ("bigram", "test"), "count": 5} in output["keywords"]
    assert {"word": ("trigram", "test", "word"), "count": 5} in output["keywords"]

    # Check total time calculation
    assert "total_time" in output
    assert output["total_time"] > 0


# Add more tests below for different scenarios (duplicates, arguments, etc.)
# For example:


@patch("pyseoanalyzer.analyzer.Website")
def test_analyze_duplicates(MockWebsite):
    # --- Setup Mock ---
    mock_site_instance = MockWebsite.return_value
    mock_page1 = create_mock_page(
        "http://example.com/page1", "Page 1", "Desc", 100, "hash_dup"
    )
    mock_page2 = create_mock_page(
        "http://example.com/page2", "Page 2", "Desc", 150, "hash_dup"
    )  # Same hash
    mock_page3 = create_mock_page(
        "http://example.com/page3", "Page 3", "Desc", 200, "hash_unique"
    )
    mock_site_instance.crawled_pages = [mock_page1, mock_page2, mock_page3]
    mock_site_instance.content_hashes = {
        "hash_dup": ["http://example.com/page1", "http://example.com/page2"],
        "hash_unique": ["http://example.com/page3"],
    }
    mock_site_instance.wordcount = {}
    mock_site_instance.bigrams = {}
    mock_site_instance.trigrams = {}

    # --- Run analyze ---
    output = analyze("http://example.com")  # Default follow_links=True

    # --- Assertions ---
    MockWebsite.assert_called_once_with(
        base_url="http://example.com",
        sitemap=None,
        analyze_headings=False,
        analyze_extra_tags=False,
        follow_links=True,  # Check default
        run_llm_analysis=False,
    )
    mock_site_instance.crawl.assert_called_once()

    assert len(output["pages"]) == 3
    assert len(output["duplicate_pages"]) == 1
    # Convert to sets for order-independent comparison
    assert set(output["duplicate_pages"][0]) == {
        "http://example.com/page1",
        "http://example.com/page2",
    }
    assert output["keywords"] == []


@patch("pyseoanalyzer.analyzer.Website")
def test_analyze_arguments_passthrough(MockWebsite):
    # --- Setup Mock ---
    mock_site_instance = MockWebsite.return_value
    mock_site_instance.crawled_pages = []
    mock_site_instance.content_hashes = {}
    mock_site_instance.wordcount = {}
    mock_site_instance.bigrams = {}
    mock_site_instance.trigrams = {}

    # --- Run analyze with specific arguments ---
    analyze(
        "http://example.com",
        sitemap_url="http://example.com/sitemap.xml",
        analyze_headings=True,
        analyze_extra_tags=True,
        follow_links=False,
        run_llm_analysis=True,
    )

    # --- Assertions ---
    # Check Website constructor call reflects arguments
    MockWebsite.assert_called_once_with(
        base_url="http://example.com",
        sitemap="http://example.com/sitemap.xml",
        analyze_headings=True,
        analyze_extra_tags=True,
        follow_links=False,
        run_llm_analysis=True,
    )
    mock_site_instance.crawl.assert_called_once()


@patch("pyseoanalyzer.analyzer.Website")
def test_analyze_keyword_filtering(MockWebsite):
    # --- Setup Mock ---
    mock_site_instance = MockWebsite.return_value
    mock_site_instance.crawled_pages = []
    mock_site_instance.content_hashes = {}
    # Include counts <= 4
    mock_site_instance.wordcount = {"high": 10, "medium": 5, "low": 4, "verylow": 3}
    mock_site_instance.bigrams = {("bi", "high"): 6, ("bi", "low"): 4}
    mock_site_instance.trigrams = {("tri", "high", "a"): 5, ("tri", "low", "b"): 3}

    # --- Run analyze ---
    output = analyze("http://example.com")

    # --- Assertions ---
    assert len(output["keywords"]) == 4  # Only counts > 4 should be included
    words_in_keywords = {kw["word"] for kw in output["keywords"]}
    assert "high" in words_in_keywords
    assert "medium" in words_in_keywords
    assert ("bi", "high") in words_in_keywords
    assert ("tri", "high", "a") in words_in_keywords
    assert "low" not in words_in_keywords
    assert "verylow" not in words_in_keywords
    assert ("bi", "low") not in words_in_keywords
    assert ("tri", "low", "b") not in words_in_keywords

    # Check sorting (descending by count)
    counts = [kw["count"] for kw in output["keywords"]]
    assert counts == sorted(counts, reverse=True)
