import json
import httpx
from typing import AsyncIterator

from app.config import get_settings
from app.services.llm.base import BaseLLMAdapter

settings = get_settings()


class QwenAdapter(BaseLLMAdapter):
    """通义千问 API 适配器。

    通过阿里云 DashScope 兼容模式接口访问，与 OpenAI 接口格式兼容。
    文档: https://help.aliyun.com/document_detail/2712195.html
    """

    def __init__(self) -> None:
        self.api_key = settings.qwen_api_key
        self.api_base = settings.qwen_api_url.rstrip("/")
        self._model = settings.qwen_model

    @property
    def model_name(self) -> str:
        return self._model

    def _build_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_payload(self, messages: list[dict], **kwargs) -> dict:
        payload: dict = {
            "model": self._model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096),
        }
        # 可选：启用 usage 统计
        if "stream_options" not in kwargs:
            payload["stream_options"] = {"include_usage": False}
        return payload

    async def chat(self, messages: list[dict], **kwargs) -> str:
        """非流式对话，返回完整回复。"""
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            resp = await client.post(
                f"{self.api_base}/chat/completions",
                headers=self._build_headers(),
                json=self._build_payload(messages, **kwargs),
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        """OpenAI 兼容流式对话，逐 token yield。"""
        payload = self._build_payload(messages, **kwargs)
        payload["stream"] = True

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            async with client.stream(
                "POST",
                f"{self.api_base}/chat/completions",
                headers=self._build_headers(),
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
