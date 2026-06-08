import os

from config.local_config import get_local_section

DEFAULT_SMTP_HOST = "smtp.qiye.aliyun.com"
DEFAULT_SMTP_PORT = 465
DEFAULT_SMTP_SENDER = "sjbi@bi-cheng.cn"


def get_smtp_config():
    local_config = get_local_section("smtp")
    password = local_config.get("password") or os.environ.get("SMTP_PASSWORD")
    if not password:
        raise RuntimeError("缺少 SMTP 密码，请在 config/local.json 或 SMTP_PASSWORD 中配置邮箱授权码。")
    return {
        "host": local_config.get("host") or os.environ.get("SMTP_HOST", DEFAULT_SMTP_HOST),
        "port": int(local_config.get("port") or os.environ.get("SMTP_PORT", DEFAULT_SMTP_PORT)),
        "sender": local_config.get("sender") or os.environ.get("SMTP_SENDER", DEFAULT_SMTP_SENDER),
        "password": password,
    }
