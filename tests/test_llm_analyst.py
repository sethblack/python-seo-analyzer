import pytest
from langchain_anthropic import ChatAnthropic
from pyseoanalyzer.llm_analyst import (
    LLMSEOEnhancer,
    ORCAROUTER_API_URL,
    ORCAROUTER_DEFAULT_MODEL,
)


@pytest.fixture
def seo_data():
    return {
        "title": "Test Title",
        "description": "Test Description",
        "keywords": ["test", "seo"],
        "content": "This is a test content.",
    }


@pytest.fixture
def anthropic_key(monkeypatch):
    monkeypatch.delenv("ORCAROUTER_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")


@pytest.fixture
def orcarouter_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("ORCAROUTER_API_KEY", "sk-orca-test")


def test_init_uses_anthropic(anthropic_key):
    enhancer = LLMSEOEnhancer()
    assert isinstance(enhancer.llm, ChatAnthropic)
    assert enhancer.llm.model == "claude-3-sonnet-20240229"
    assert enhancer.llm.temperature == 0


def test_init_uses_orcarouter_when_configured(orcarouter_key):
    enhancer = LLMSEOEnhancer()
    assert isinstance(enhancer.llm, ChatAnthropic)
    assert enhancer.llm.model == ORCAROUTER_DEFAULT_MODEL
    assert enhancer.llm.anthropic_api_url == ORCAROUTER_API_URL
    assert enhancer.llm.temperature == 0


def test_init_orcarouter_honors_model_override(orcarouter_key, monkeypatch):
    monkeypatch.setenv("ORCAROUTER_MODEL", "openai/gpt-4o")
    enhancer = LLMSEOEnhancer()
    assert enhancer.llm.model == "openai/gpt-4o"
    assert enhancer.llm.anthropic_api_url == ORCAROUTER_API_URL


@pytest.mark.asyncio
async def test_enhance_seo_analysis(anthropic_key, seo_data):
    enhancer = LLMSEOEnhancer()
    result = await enhancer.enhance_seo_analysis(seo_data)

    assert "summary" in result

    assert "entity_analysis" in result["detailed_analysis"]
    assert "credibility_analysis" in result["detailed_analysis"]
    assert "conversation_analysis" in result["detailed_analysis"]
    assert "cross_platform_presence" in result["detailed_analysis"]
    assert "recommendations" in result["detailed_analysis"]
