"""日志处理器。

对 LogRecord 进行转换、增强、清理等预处理。
"""

import re

from src.logging.pipeline import Processor
from src.logging.schema import LogRecord


class Enricher(Processor):
    """增强处理器：添加额外上下文信息到 payload。"""

    def __init__(self, extra: dict | None = None) -> None:
        self._extra = extra or {}

    def process(self, record: LogRecord) -> None:
        if self._extra:
            record.payload.update(self._extra)


class Sanitizer(Processor):
    """清理处理器：过滤敏感信息。"""

    SENSITIVE_PATTERNS = [
        (r"(sk-[a-zA-Z0-9]{20,})", r"sk-***"),
        (r"(api_key['\"]?\s*[:=]\s*['\"])[^'\"]+(['\"])", r"\1***\2"),
        (r"(token['\"]?\s*[:=]\s*['\"])[^'\"]+(['\"])", r"\1***\2"),
        (r"(password['\"]?\s*[:=]\s*['\"])[^'\"]+(['\"])", r"\1***\2"),
        (r"(secret['\"]?\s*[:=]\s*['\"])[^'\"]+(['\"])", r"\1***\2"),
    ]
    SENSITIVE_KEYS = {"api_key", "api-key", "token", "password", "secret"}

    def process(self, record: LogRecord) -> None:
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            record.message = re.sub(pattern, replacement, record.message)
        self._sanitize_dict(record.payload)

    def _sanitize_dict(self, d: dict) -> None:
        for key in list(d.keys()):
            value = d[key]
            if isinstance(value, str):
                if key.lower() in self.SENSITIVE_KEYS:
                    d[key] = "***"
                else:
                    for pattern, replacement in self.SENSITIVE_PATTERNS:
                        d[key] = re.sub(pattern, replacement, value)
            elif isinstance(value, dict):
                self._sanitize_dict(value)
