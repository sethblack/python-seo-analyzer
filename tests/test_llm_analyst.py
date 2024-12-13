import pytest
from pyseoanalyzer.llm_analyst import LLMSEOEnhancer
from langchain_anthropic import ChatAnthropic
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import json


@pytest.fixture
def seo_data():
    return {
        "title": "Test Title",
        "description": "Test Description",
        "keywords": ["test", "seo"],
        "content": "This is a test content.",
    }


def test_init():
    enhancer = LLMSEOEnhancer()
    assert isinstance(enhancer.llm, ChatAnthropic)
    assert enhancer.llm.model == "claude-3-sonnet-20240229"
    assert enhancer.llm.temperature == 0


@pytest.mark.asyncio
async def test_enhance_seo_analysis(seo_data):
    enhancer = LLMSEOEnhancer()
    result = await enhancer.enhance_seo_analysis(seo_data)

    assert "summary" in result

    assert "entity_analysis" in result["detailed_analysis"]
    assert "credibility_analysis" in result["detailed_analysis"]
    assert "conversation_analysis" in result["detailed_analysis"]
    assert "cross_platform_presence" in result["detailed_analysis"]
    assert "recommendations" in result["detailed_analysis"]
