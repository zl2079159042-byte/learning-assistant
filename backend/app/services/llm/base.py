from abc import ABC, abstractmethod
from typing import AsyncIterator


class BaseLLMAdapter(ABC):
    """LLM 适配器统一基类。

    所有大模型适配器必须实现此接口：

    - chat_stream: 流式对话，逐 token yield，用于 SSE 实时推送。
    - chat: 非流式对话，返回完整回复。
    - model_name: 返回当前适配器使用的模型名称。
    """

    @abstractmethod
    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        """流式对话。

        逐 token yield 字符串块，调用方通过 async for 消费。

        Args:
            messages: OpenAI 兼容格式的消息列表 [{"role": ..., "content": ...}, ...]
            **kwargs: 额外参数，如 temperature, max_tokens 等

        Yields:
            str: 每次 yield 一个 token 片段
        """
        raise NotImplementedError

    @abstractmethod
    async def chat(self, messages: list[dict], **kwargs) -> str:
        """非流式对话，返回完整回复文本。

        Args:
            messages: OpenAI 兼容格式的消息列表
            **kwargs: 额外参数

        Returns:
            str: 模型生成的完整回复
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def model_name(self) -> str:
        """当前适配器使用的模型名称。"""
        raise NotImplementedError
