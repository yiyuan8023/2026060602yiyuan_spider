import os

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)
DEFAULT_EMAIL = "yiyuan@bi-cheng.cn"


def _get_log_mode():
    # LOG_MODE=file 仅记录文件，LOG_MODE=console 仅记录控制台，LOG_MODE=both 同时记录文件和控制台
    log_mode = os.environ.get("LOG_MODE", "").strip().lower()
    if log_mode not in {"file", "console", "both"}:
        return "both"
    return log_mode


UA = os.environ.get("YIYUAN_UA", DEFAULT_UA)
EMAIL = os.environ.get("YIYUAN_EMAIL", DEFAULT_EMAIL)
LOG_MODE = _get_log_mode()
