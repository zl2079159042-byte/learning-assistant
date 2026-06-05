from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Application
    app_name: str = "Learning Assistant"
    debug: bool = False
    database_url: str = "sqlite+aiosqlite:///./learning_assistant.db"

    # Default LLM to use when not specified by the caller
    default_model: str = "qwen"

    # Qwen / Tongyi Qianwen
    qwen_api_key: str = ""
    qwen_api_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen-turbo"

    # Wenxin / Baidu Qianfan
    wenxin_api_key: str = ""
    wenxin_secret_key: str = ""
    wenxin_api_url: str = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat"
    wenxin_model: str = "ernie-speed-128k"

    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_api_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"


@lru_cache
def get_settings() -> Settings:
    return Settings()
