import json
import sys
import types
from types import SimpleNamespace
from unittest import mock

import pytest
from langchain_core.messages import HumanMessage, SystemMessage

from pyseoanalyzer.litellm_chat import LiteLLMChat
from pyseoanalyzer.llm_analyst import LLMSEOEnhancer, ORCAROUTER_API_URL


def _response(content, model="gemini-2.5-flash"):
    return SimpleNamespace(
        model=model,
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content), finish_reason="stop"
            )
        ],
        usage=SimpleNamespace(prompt_tokens=12, completion_tokens=5, total_tokens=17),
    )


@pytest.fixture
def fake_litellm(monkeypatch):
    """A stand-in litellm module so the tests run without the optional extra."""
    fake = types.ModuleType("litellm")
    fake.completion = mock.MagicMock(name="litellm.completion")
    fake.acompletion = mock.AsyncMock(name="litellm.acompletion")
    monkeypatch.setitem(sys.modules, "litellm", fake)
    return fake


@pytest.fixture
def litellm_env(monkeypatch):
    for name in (
        "ORCAROUTER_API_KEY",
        "UBERLLM_API_KEY",
        "ANTHROPIC_API_KEY",
        "LITELLM_API_BASE",
        "LITELLM_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("LITELLM_MODEL", "gemini/gemini-2.5-flash")


def test_invoke_sends_openai_messages_with_drop_params(fake_litellm):
    fake_litellm.completion.return_value = _response("OK")
    chat = LiteLLMChat(model="gemini/gemini-2.5-flash")

    reply = chat.invoke(
        [SystemMessage(content="Be brief."), HumanMessage(content="Hi")]
    )

    assert reply.content == "OK"
    assert reply.usage_metadata == {
        "input_tokens": 12,
        "output_tokens": 5,
        "total_tokens": 17,
    }
    assert reply.response_metadata["finish_reason"] == "stop"
    kwargs = fake_litellm.completion.call_args.kwargs
    assert kwargs["model"] == "gemini/gemini-2.5-flash"
    assert kwargs["messages"] == [
        {"role": "system", "content": "Be brief."},
        {"role": "user", "content": "Hi"},
    ]
    assert kwargs["drop_params"] is True
    assert kwargs["temperature"] == 0
    assert kwargs["num_retries"] == 3
    assert kwargs["timeout"] == 30
    # No key or base unless configured, so LiteLLM reads the provider's own
    # environment variables (GEMINI_API_KEY, AWS credentials, ...).
    assert "api_key" not in kwargs
    assert "api_base" not in kwargs


def test_proxy_settings_stop_and_drop_params_opt_out(fake_litellm):
    fake_litellm.completion.return_value = _response(None)
    chat = LiteLLMChat(
        model="gpt-4.1-mini",
        api_base="http://localhost:4000",
        api_key="sk-proxy",
        temperature=None,
        drop_params=False,
    )

    reply = chat.invoke("Hi", stop=["\n\n"])

    assert reply.content == ""
    kwargs = fake_litellm.completion.call_args.kwargs
    assert kwargs["api_base"] == "http://localhost:4000"
    assert kwargs["api_key"] == "sk-proxy"
    assert kwargs["stop"] == ["\n\n"]
    assert kwargs["drop_params"] is False
    assert "temperature" not in kwargs


def test_proxy_models_ask_the_proxy_to_drop_params(fake_litellm):
    fake_litellm.completion.return_value = _response("OK")

    LiteLLMChat(model="litellm_proxy/gpt-5-nano").invoke("Hi")
    assert fake_litellm.completion.call_args.kwargs["extra_body"] == {
        "drop_params": True
    }

    # Other providers drop parameters client-side; real OpenAI-compatible
    # endpoints would reject an unknown drop_params body field.
    LiteLLMChat(model="openai/gpt-5-nano").invoke("Hi")
    assert "extra_body" not in fake_litellm.completion.call_args.kwargs
    LiteLLMChat(model="litellm_proxy/gpt-5-nano", drop_params=False).invoke("Hi")
    assert "extra_body" not in fake_litellm.completion.call_args.kwargs


def test_feedback_banner_is_suppressed(fake_litellm):
    fake_litellm.completion.return_value = _response("OK")
    fake_litellm.suppress_debug_info = False

    LiteLLMChat(model="gemini/gemini-2.5-flash").invoke("Hi")

    assert fake_litellm.suppress_debug_info is True


@pytest.mark.asyncio
async def test_ainvoke_uses_acompletion(fake_litellm):
    fake_litellm.acompletion.return_value = _response("async OK")
    chat = LiteLLMChat(model="bedrock/anthropic.claude-sonnet-4-6")

    reply = await chat.ainvoke("Hi")

    assert reply.content == "async OK"
    fake_litellm.completion.assert_not_called()
    assert fake_litellm.acompletion.call_args.kwargs["model"] == (
        "bedrock/anthropic.claude-sonnet-4-6"
    )


def test_missing_litellm_names_the_extra(monkeypatch):
    monkeypatch.setitem(sys.modules, "litellm", None)
    chat = LiteLLMChat(model="gemini/gemini-2.5-flash")

    with pytest.raises(ImportError, match=r"pyseoanalyzer\[litellm\]"):
        chat.invoke("Hi")


def test_enhancer_uses_litellm_when_model_is_set(litellm_env, monkeypatch):
    monkeypatch.setenv("LITELLM_API_BASE", "http://localhost:4000")
    monkeypatch.setenv("LITELLM_API_KEY", "sk-proxy")

    enhancer = LLMSEOEnhancer()

    assert isinstance(enhancer.llm, LiteLLMChat)
    assert enhancer.llm.model == "gemini/gemini-2.5-flash"
    assert enhancer.llm.api_base == "http://localhost:4000"
    assert enhancer.llm.api_key == "sk-proxy"
    assert enhancer.llm.temperature == 0


def test_enhancer_litellm_ignores_blank_proxy_settings(litellm_env, monkeypatch):
    monkeypatch.setenv("LITELLM_API_BASE", "")
    monkeypatch.setenv("LITELLM_API_KEY", "")

    enhancer = LLMSEOEnhancer()

    assert enhancer.llm.api_base is None
    assert enhancer.llm.api_key is None


def test_litellm_model_takes_precedence_over_gateway_keys(litellm_env, monkeypatch):
    monkeypatch.setenv("ORCAROUTER_API_KEY", "sk-orca-test")
    assert isinstance(LLMSEOEnhancer().llm, LiteLLMChat)

    monkeypatch.delenv("LITELLM_MODEL")
    enhancer = LLMSEOEnhancer()
    assert not isinstance(enhancer.llm, LiteLLMChat)
    assert enhancer.llm.anthropic_api_url == ORCAROUTER_API_URL


ANALYSIS_REPLIES = {
    "entity optimization:": {
        "entity_assessment": "Clear brand entity",
        "knowledge_panel_readiness": 70,
        "key_improvements": ["Add Organization schema"],
    },
    "credibility aspects:": {
        "credibility_assessment": "Solid",
        "neeat_scores": {
            "notability": 6,
            "experience": 6,
            "expertise": 6,
            "authoritativeness": 6,
            "trustworthiness": 6,
            "transparency": 6,
        },
        "trust_signals": ["About page"],
    },
    "conversational search readiness:": {
        "conversation_readiness": "Partial",
        "query_patterns": ["what is"],
        "engagement_score": 55,
        "gaps": ["No FAQ"],
    },
    "presence across different platforms:": {
        "platform_coverage": {"search": "good"},
        "visibility_scores": {"search": 80, "social": 40},
        "optimization_opportunities": ["Publish on LinkedIn"],
    },
    "strategic recommendations:": {
        "strategic_recommendations": ["Build topical authority"],
        "quick_wins": ["Add meta descriptions"],
        "long_term_strategy": ["Earn citations"],
        "priority_matrix": {"meta descriptions": "high impact, low effort"},
    },
}


@pytest.mark.asyncio
async def test_full_analysis_runs_through_litellm(litellm_env, fake_litellm, seo_page):
    async def reply(**kwargs):
        prompt = kwargs["messages"][-1]["content"]
        for marker, payload in ANALYSIS_REPLIES.items():
            if marker in prompt:
                return _response(json.dumps(payload))
        raise AssertionError(f"unexpected prompt: {prompt[:80]}")

    fake_litellm.acompletion.side_effect = reply

    result = await LLMSEOEnhancer().enhance_seo_analysis(seo_page)

    assert fake_litellm.acompletion.call_count == 5
    assert result["summary"]["entity_score"] == 70
    assert result["summary"]["credibility_score"] == 6
    assert result["summary"]["platform_score"] == 60
    assert result["quick_wins"] == ["Add meta descriptions"]


@pytest.fixture
def seo_page():
    return {
        "title": "Test Title",
        "description": "Test Description",
        "keywords": ["test", "seo"],
        "content": "This is a test content.",
    }
