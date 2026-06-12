# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一贯
- 创建时间：2026-06-11 06:29:55
- 最近修改：2026-06-11 06:29:55
- 文件用途：提供钉钉 API 公共配置读取、Secret 脱敏、Webhook 加签和基础异常类型。
- 业务范围：适用于 API_DingTalk 下 Webhook 发消息、Stream 回复、在线表格读取和任务通知模块。
- 依赖入口：使用 os、time、hmac、hashlib、base64、urllib.parse、pathlib 和 config.local_config。
- 验收方式：修改后执行 py_compile，并执行 API.API_DingTalk.API_DingTalk_Base 导入探针。
- 注意事项：配置读取只返回必要字段；日志和异常不得输出完整 Secret、Webhook 签名或钉钉访问令牌。
"""

import base64
import hashlib
import hmac
import os
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from config.local_config import get_local_section


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = PROJECT_ROOT / "state"
DEFAULT_TIMEOUT = 20


class DingTalkApiError(RuntimeError):
    """钉钉 API 调用失败。"""


class DingTalkConfigError(RuntimeError):
    """钉钉本地配置缺失或仍是占位符。"""


def load_dingtalk_section() -> dict[str, Any]:
    """读取 config/local.json 中的 dingtalk 配置段。"""
    return get_local_section("dingtalk")


def parse_bool(value: Any, default: bool = False) -> bool:
    """把环境变量或本地配置里的布尔值转成 bool。"""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return default


def get_config_value(
    env_names: str | list[str],
    local_key: str,
    default: Any = None,
    *,
    section: dict[str, Any] | None = None,
) -> Any:
    """按环境变量优先、本地配置兜底的顺序读取钉钉配置。"""
    names = [env_names] if isinstance(env_names, str) else env_names
    for env_name in names:
        value = os.getenv(env_name)
        if value not in (None, ""):
            return value

    local_section = section if section is not None else load_dingtalk_section()
    value = local_section.get(local_key)
    if value not in (None, ""):
        return value
    return default


def require_config_value(value: Any, name: str) -> str:
    """校验必填配置，防止占位符进入真实请求。"""
    text = str(value or "").strip()
    if not text:
        raise DingTalkConfigError(f"缺少钉钉配置：{name}")
    if text.startswith("your_") or text in {"钉钉机器人Webhook", "钉钉机器人Secret"}:
        raise DingTalkConfigError(f"钉钉配置仍是占位符：{name}")
    return text


def mask_secret(value: str | None, left: int = 6, right: int = 4) -> str:
    """脱敏显示敏感值，用于安全日志。"""
    if not value:
        return ""
    if len(value) <= left + right:
        return "*" * len(value)
    return f"{value[:left]}{'*' * 6}{value[-right:]}"


def build_signed_webhook_url(webhook: str, secret: str | None) -> str:
    """为开启加签的自定义机器人 Webhook 追加 timestamp 和 sign。"""
    if not secret:
        return webhook

    timestamp = str(round(time.time() * 1000))
    string_to_sign = f"{timestamp}\n{secret}".encode("utf-8")
    secret_bytes = secret.encode("utf-8")
    sign = quote_plus(base64.b64encode(hmac.new(secret_bytes, string_to_sign, digestmod=hashlib.sha256).digest()))
    separator = "&" if "?" in webhook else "?"
    return f"{webhook}{separator}timestamp={timestamp}&sign={sign}"


def ensure_state_dir() -> Path:
    """确保项目运行状态目录存在。"""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR
