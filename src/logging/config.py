"""日志配置管理（pydantic-settings）。

配置项通过环境变量 LOG_* 或 .env 文件设置。
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class LogConfig(BaseSettings):
    """日志系统配置。

    用法::
        config = LogConfig()
        # 环境变量覆盖: LOG_LEVEL=DEBUG LOG_FORMAT=json
    """
    model_config = {"env_prefix": "LOG_"}

    level: str = Field(default="INFO", description="TRACE/DEBUG/INFO/WARNING/ERROR")
    format: str = Field(default="json", description="json / text")
    output: str = Field(default="console", description="console / file / both")
    dir: str = Field(default="./logs", description="日志目录")
    file_name: str = Field(default="agent.log", description="日志文件名")
    rotation: str = Field(default="500 MB", description="文件轮转大小")
    retention: str = Field(default="30 days", description="日志保留时间")
    json_indent: int | None = Field(default=None, description="JSON 缩进")
    enable_otel: bool = Field(default=False, description="启用 OTel")
    enable_replay: bool = Field(default=False, description="启用 Replay")
    otel_endpoint: str = Field(default="http://localhost:4317", description="OTel 端点")
