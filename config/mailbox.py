"""
开发说明：
- 作者：Codex
- 创建时间：2026-06-13 16:03:00
- 最近修改：2026-06-13 19:18:25
- 文件用途：统一读取邮箱 IMAP 配置，优先服务 163 邮箱验证码抓取场景，同时保留环境变量兜底能力。
- 业务范围：适用于项目内所有需要读取邮箱正文、邮件摘要、验证码的公共模块或执行脚本。
- 依赖入口：使用标准库 os，复用 config.local_config.get_local_section 读取本地私有配置。
- 验收方式：修改后执行 py_compile；分别验证 local.json 和环境变量两种配置路径都能正常返回配置对象或给出明确报错。
- 注意事项：不得提交真实邮箱账号、授权码或其他敏感信息；日志和异常信息中不得回显完整密钥。
"""

import os

from config.local_config import get_local_section


DEFAULT_MAILBOX_HOST = "imap.163.com"
DEFAULT_MAILBOX_PORT = 993
DEFAULT_MAILBOX_FOLDER = "INBOX"
DEFAULT_MAILBOX_TIMEOUT = 30


def _get_bool_value(raw_value, default=True):
    """把本地配置或环境变量中的布尔值转成 Python bool。"""
    if raw_value is None:
        return default
    if isinstance(raw_value, bool):
        return raw_value
    return str(raw_value).strip().lower() in {"1", "true", "yes", "on"}


def get_mailbox_config():
    """读取邮箱 IMAP 配置，优先 local.json，其次环境变量。"""
    local_config = get_local_section("mailbox")
    username = (
        local_config.get("username")
        or os.environ.get("MAILBOX_USERNAME")
        or os.environ.get("MAILBOX_ACCOUNT")
    )
    password = (
        local_config.get("password")
        or os.environ.get("MAILBOX_PASSWORD")
        or os.environ.get("MAILBOX_AUTH_CODE")
    )

    if not username:
        raise RuntimeError(
            "缺少邮箱账号，请在 config/local.json 的 其他.username 或 MAILBOX_USERNAME 中配置。"
        )
    if not password:
        raise RuntimeError(
            "缺少邮箱授权码，请在 config/local.json 的 其他.password 或 MAILBOX_PASSWORD 中配置。"
        )

    return {
        "protocol": "imap",
        "host": local_config.get("host") or os.environ.get("MAILBOX_HOST", DEFAULT_MAILBOX_HOST),
        "port": int(local_config.get("port") or os.environ.get("MAILBOX_PORT", DEFAULT_MAILBOX_PORT)),
        "username": username,
        "password": password,
        "folder": local_config.get("folder") or os.environ.get("MAILBOX_FOLDER", DEFAULT_MAILBOX_FOLDER),
        "use_ssl": _get_bool_value(
            local_config.get("use_ssl", os.environ.get("MAILBOX_USE_SSL")),
            default=True,
        ),
        "timeout": int(
            local_config.get("timeout") or os.environ.get("MAILBOX_TIMEOUT", DEFAULT_MAILBOX_TIMEOUT)
        ),
    }
