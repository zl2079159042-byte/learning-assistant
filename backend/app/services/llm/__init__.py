"""LLM 适配器工厂模块。

提供:
- get_adapter(model): 按名称获取/缓存适配器实例 ("deepseek" | "qwen" | "wenxin")
- get_default_adapter(): 返回配置中 default_model 对应的适配器
- BaseLLMAdapter: 抽象基类
"""

from app.services.llm.base import BaseLLMAdapter
from app.services.llm.deepseek import DeepSeekAdapter
from app.services.llm.qwen import QwenAdapter
from app.services.llm.wenxin import WenxinAdapter

__all__ = [
    "BaseLLMAdapter",
    "DeepSeekAdapter",
    "QwenAdapter",
    "WenxinAdapter",
    "get_adapter",
    "get_default_adapter",
]

_ADAPTER_REGISTRY: dict[str, type[BaseLLMAdapter]] = {
    "deepseek": DeepSeekAdapter,
    "qwen": QwenAdapter,
    "wenxin": WenxinAdapter,
}

_adapters: dict[str, BaseLLMAdapter] = {}


def get_adapter(model: str) -> BaseLLMAdapter:
    """根据模型名称获取或创建适配器实例（单例缓存）。

    Args:
        model: 模型标识符，支持 "deepseek", "qwen", "wenxin"

    Returns:
        BaseLLMAdapter 实例

    Raises:
        ValueError: 未知的模型名称
    """
    model = model.lower().strip()
    if model not in _ADAPTER_REGISTRY:
        raise ValueError(
            f"未知的模型: '{model}'，可用模型: {list(_ADAPTER_REGISTRY.keys())}"
        )

    if model not in _adapters:
        _adapters[model] = _ADAPTER_REGISTRY[model]()

    return _adapters[model]


def get_default_adapter() -> BaseLLMAdapter:
    """返回配置中默认模型对应的适配器。"""
    from app.config import get_settings

    return get_adapter(get_settings().default_model)
