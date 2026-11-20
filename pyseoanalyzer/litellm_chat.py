"""LangChain chat model backed by the LiteLLM SDK.

LiteLLM (https://docs.litellm.ai) calls 100+ model providers (OpenAI, Gemini,
Vertex AI, Bedrock, Azure, Mistral, Ollama, a LiteLLM proxy, ...) through one
``completion`` call, using ``provider/model`` ids such as
``gemini/gemini-2.5-flash``. Wrapping it as a LangChain chat model lets the AI
optimization chains run on any of them unchanged.

The module is not named ``litellm.py`` on purpose: running
``python pyseoanalyzer/__main__.py`` puts this directory on ``sys.path``, where
a local ``litellm.py`` would shadow the real package.
"""

from typing import Any, Dict, List, Optional

from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

# LangChain message types to OpenAI-style roles, which LiteLLM expects.
_ROLES = {"human": "user", "ai": "assistant", "system": "system"}


def _import_litellm():
    try:
        import litellm
    except ImportError as exc:
        raise ImportError(
            "LITELLM_MODEL is set but the litellm package is not installed. "
            "Install it with: pip install 'pyseoanalyzer[litellm]'"
        ) from exc
    # LiteLLM prints a "Give Feedback / Get Help" banner to stdout on every
    # failed call, which would corrupt `--output-format json` output.
    litellm.suppress_debug_info = True
    return litellm


class LiteLLMChat(BaseChatModel):
    """Chat model that sends LangChain messages through ``litellm.completion``.

    Credentials come from each provider's usual environment variables
    (``OPENAI_API_KEY``, ``GEMINI_API_KEY``, AWS credentials, ...) unless
    ``api_key`` is set. ``api_base`` points requests at a LiteLLM proxy or any
    other custom endpoint.
    """

    model: str
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    temperature: Optional[float] = 0
    timeout: float = 30
    max_retries: int = 3
    # Providers reject parameters they do not support (e.g. reasoning models
    # refuse temperature=0); LiteLLM drops those instead of failing the call.
    drop_params: bool = True

    @property
    def _llm_type(self) -> str:
        return "litellm"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model": self.model, "api_base": self.api_base}

    def _completion_params(
        self, messages: List[BaseMessage], stop: Optional[List[str]], **kwargs: Any
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": _ROLES.get(message.type, "user"), "content": message.content}
                for message in messages
            ],
            "timeout": self.timeout,
            # LiteLLM only retries transient failures (rate limits, timeouts,
            # connection errors), never authentication or validation errors.
            "num_retries": self.max_retries,
            "drop_params": self.drop_params,
        }
        if self.temperature is not None:
            params["temperature"] = self.temperature
        if stop:
            params["stop"] = stop
        if self.api_base:
            params["api_base"] = self.api_base
        if self.api_key:
            params["api_key"] = self.api_key
        if self.drop_params and self.model.startswith("litellm_proxy/"):
            # Requests to a LiteLLM proxy are passed through as-is, so the
            # proxy has to drop unsupported parameters itself.
            params["extra_body"] = {"drop_params": True}
        params.update(kwargs)
        return params

    @staticmethod
    def _to_result(response: Any) -> ChatResult:
        choice = response.choices[0]
        message = AIMessage(
            content=choice.message.content or "",
            response_metadata={
                "model": getattr(response, "model", None),
                "finish_reason": getattr(choice, "finish_reason", None),
            },
        )
        usage = getattr(response, "usage", None)
        if usage is not None:
            message.usage_metadata = {
                "input_tokens": usage.prompt_tokens or 0,
                "output_tokens": usage.completion_tokens or 0,
                "total_tokens": usage.total_tokens or 0,
            }
        return ChatResult(generations=[ChatGeneration(message=message)])

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        litellm = _import_litellm()
        response = litellm.completion(
            **self._completion_params(messages, stop, **kwargs)
        )
        return self._to_result(response)

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        litellm = _import_litellm()
        response = await litellm.acompletion(
            **self._completion_params(messages, stop, **kwargs)
        )
        return self._to_result(response)
