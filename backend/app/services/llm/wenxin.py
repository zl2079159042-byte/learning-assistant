import json
import httpx
from typing import AsyncIterator

from app.config import get_settings
from app.services.llm.base import BaseLLMAdapter

settings = get_settings()

WENXIN_OAUTH_URL = "https://aip.baidubce.com/oauth/2.0/token"
WENXIN_CHAT_URL_TEMPLATE = (
    "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{model}"
)


class WenxinAdapter(BaseLLMAdapter):
    """文心一言 API 适配器。

    百度文心使用 OAuth 2.0 Client Credentials 流程获取 access_token，
    之后所有对话请求需附带该 token。token 有过期时间，此适配器会在失效
    时自动刷新。

    文档: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/jlil56u11
    """

    def __init__(self) -> None:
        self.api_key = settings.wenxin_api_key
        self.secret_key = settings.wenxin_secret_key
        self._model = settings.wenxin_model
        self._access_token: str | None = None

    @property
    def model_name(self) -> str:
        return self._model

    async def _get_access_token(self) -> str:
        """获取或刷新 Baidu OAuth access_token。"""
        if self._access_token:
            return self._access_token

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            resp = await client.post(
                WENXIN_OAUTH_URL,
                params={
                    "grant_type": "client_credentials",
                    "client_id": self.api_key,
                    "client_secret": self.secret_key,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                raise RuntimeError(
                    f"百度 OAuth 认证失败: {data.get('error_description', data['error'])}"
                )
            self._access_token = data["access_token"]
            return self._access_token

    def _invalidate_token(self) -> None:
        """标记 token 失效，下次请求会重新获取。"""
        self._access_token = None

    def _build_url(self, token: str) -> str:
        url = WENXIN_CHAT_URL_TEMPLATE.format(model=self._model)
        return f"{url}?access_token={token}"

    def _build_payload(self, messages: list[dict], **kwargs) -> dict:
        return {
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_output_tokens": kwargs.get("max_tokens", 4096),
        }

    async def chat(self, messages: list[dict], **kwargs) -> str:
        """非流式对话，返回完整回复。"""
        token = await self._get_access_token()

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            resp = await client.post(
                self._build_url(token),
                json=self._build_payload(messages, **kwargs),
                headers={"Content-Type": "application/json"},
            )

            # token 过期时刷新并重试一次
            if resp.status_code == 401 or (
                resp.status_code == 200 and resp.json().get("error_code") == 110
            ):
                self._invalidate_token()
                token = await self._get_access_token()
                resp = await client.post(
                    self._build_url(token),
                    json=self._build_payload(messages, **kwargs),
                    headers={"Content-Type": "application/json"},
                )

            resp.raise_for_status()
            data = resp.json()
            if "error_code" in data:
                raise RuntimeError(
                    f"文心 API 错误 (code={data['error_code']}): {data.get('error_msg', '未知错误')}"
                )
            return data["result"]

    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        """流式对话，逐 token yield。

        文心流式响应格式与 OpenAI SSE 类似：
        - 每行以 `data: ` 开头
        - JSON 中包含 `result` 字段存放本次增量文本
        - 最后会有一条 `is_end: true` 的消息
        """
        token = await self._get_access_token()
        payload = self._build_payload(messages, **kwargs)
        payload["stream"] = True

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            async with client.stream(
                "POST",
                self._build_url(token),
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as resp:
                # token 过期重试
                if resp.status_code == 401:
                    self._invalidate_token()
                    token = await self._get_access_token()
                    async with client.stream(
                        "POST",
                        self._build_url(token),
                        json=payload,
                        headers={"Content-Type": "application/json"},
                    ) as resp2:
                        resp2.raise_for_status()
                        async for chunk_text in self._parse_stream(resp2):
                            yield chunk_text
                    return

                resp.raise_for_status()
                async for chunk_text in self._parse_stream(resp):
                    yield chunk_text

    async def _parse_stream(self, resp) -> AsyncIterator[str]:
        """解析文心流式响应行。"""
        async for line in resp.aiter_lines():
            if not line.startswith("data: "):
                continue
            data_str = line[6:]
            if not data_str.strip():
                continue
            try:
                chunk = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            # 检查是否为结束标记
            if chunk.get("is_end", False):
                break

            # 检查错误
            if "error_code" in chunk:
                raise RuntimeError(
                    f"文心流式 API 错误 (code={chunk['error_code']}): "
                    f"{chunk.get('error_msg', '未知错误')}"
                )

            content = chunk.get("result", "")
            if content:
                yield content
