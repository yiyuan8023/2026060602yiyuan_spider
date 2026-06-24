# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一贯
- 创建时间：2026-06-11 06:29:55
- 最近修改：2026-06-15 15:58:02
- 文件用途：封装钉钉任务通知模板，重点支持 run_job.py 任务异常后的机器人告警。
- 业务范围：适用于本项目 jobs 任务、调度器和手动脚本的失败通知、成功通知和简短运行摘要通知。
- 依赖入口：使用 pathlib、traceback、API_DingTalk_Base 和 API_DingTalk_Message。
- 验收方式：修改后执行 py_compile；使用无真实 Webhook 的禁用配置探针验证通知入口不会影响任务主流程。
- 注意事项：通知正文只放任务路径、异常类型、异常摘要和 traceback 尾部，不输出 Cookie、数据库密码、Webhook 或授权令牌。
"""

import traceback
from pathlib import Path
from typing import Any

from API.API_DingTalk.API_DingTalk_Base import get_config_value, load_dingtalk_section, parse_bool
from API.API_DingTalk.API_DingTalk_Message import DingTalkWebhookSender


MAX_MARKDOWN_LENGTH = 3600
MAX_TRACEBACK_LINES = 18


def _split_mobiles(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value).replace(";", ",").split(",") if item.strip()]


def _truncate(text: str, limit: int = MAX_MARKDOWN_LENGTH) -> str:
    if len(text) <= limit:
        return text
    return f"{text[: limit - 80]}\n\n> 内容过长，已截断，只保留前 {limit} 字符。"


def _tail_traceback(traceback_text: str | None) -> str:
    if not traceback_text:
        return ""
    lines = traceback_text.strip().splitlines()
    return "\n".join(lines[-MAX_TRACEBACK_LINES:])


def _normalize_keyword(value: Any) -> str:
    return str(value or "").strip()


class DingTalkJobNotifier:
    """任务运行结果钉钉通知器。"""

    def __init__(
        self,
        sender: DingTalkWebhookSender | None = None,
        *,
        enabled: bool = False,
        at_mobiles: list[str] | None = None,
        is_at_all: bool = False,
        use_card: bool = False,
        notify_keyword: str = "",
    ) -> None:
        self.sender = sender
        self.enabled = enabled
        self.at_mobiles = at_mobiles or []
        self.is_at_all = is_at_all
        self.use_card = use_card
        self.notify_keyword = _normalize_keyword(notify_keyword)

    @classmethod
    def from_config(cls, *, enabled_override: bool | None = None) -> "DingTalkJobNotifier":
        """从环境变量或 config/local.json 读取通知配置。"""
        section = load_dingtalk_section()
        enabled_value = get_config_value("DINGTALK_NOTIFY_ENABLED", "notify_enabled", False, section=section)
        enabled = parse_bool(enabled_value, default=False) if enabled_override is None else enabled_override
        at_mobiles = _split_mobiles(
            get_config_value("DINGTALK_NOTIFY_AT_MOBILES", "notify_at_mobiles", [], section=section)
        )
        is_at_all = parse_bool(
            get_config_value("DINGTALK_NOTIFY_IS_AT_ALL", "notify_is_at_all", False, section=section),
            default=False,
        )
        use_card = parse_bool(
            get_config_value("DINGTALK_NOTIFY_USE_CARD", "notify_use_card", False, section=section),
            default=False,
        )
        notify_keyword = _normalize_keyword(
            get_config_value("DINGTALK_NOTIFY_KEYWORD", "notify_keyword", "", section=section)
        )
        sender = DingTalkWebhookSender() if enabled else None
        return cls(
            sender=sender,
            enabled=enabled,
            at_mobiles=at_mobiles,
            is_at_all=is_at_all,
            use_card=use_card,
            notify_keyword=notify_keyword,
        )

    def _apply_keyword(self, title: str, text: str) -> tuple[str, str]:
        """满足钉钉机器人关键词安全策略。"""
        if not self.notify_keyword:
            return title, text
        if self.notify_keyword in title or self.notify_keyword in text:
            return title, text
        return f"{self.notify_keyword} {title}", f"**{self.notify_keyword}**\n\n{text}"

    def send_markdown(self, title: str, text: str) -> dict[str, Any] | None:
        """按通知配置发送 Markdown。"""
        if not self.enabled or not self.sender:
            return None
        title, text = self._apply_keyword(title, text)
        return self.sender.send_markdown(
            title,
            _truncate(text),
            at_mobiles=self.at_mobiles,
            is_at_all=self.is_at_all,
        )

    def send_job_failed(
        self,
        job_path: str | Path,
        exc: BaseException,
        *,
        traceback_text: str | None = None,
    ) -> dict[str, Any] | None:
        """发送任务失败通知。"""
        job_text = str(job_path)
        exc_type = type(exc).__name__
        exc_text = str(exc) or repr(exc)
        traceback_tail = _tail_traceback(traceback_text)
        title = f"任务失败：{Path(job_text).name}"
        text = (
            f"### {title}\n\n"
            f"- 任务：`{job_text}`\n"
            f"- 异常类型：`{exc_type}`\n"
            f"- 异常摘要：{exc_text}\n\n"
        )
        if traceback_tail:
            text += f"```text\n{traceback_tail}\n```\n"

        if not self.enabled or not self.sender:
            return None
        if self.use_card:
            title, text = self._apply_keyword(title, text)
            return self.sender.send_action_card(title=title, text=_truncate(text), single_title="我知道了", single_url="")
        return self.send_markdown(title, text)

    def send_job_success(self, job_path: str | Path, summary: str = "任务执行完成") -> dict[str, Any] | None:
        """发送任务成功通知。"""
        title = f"任务完成：{Path(str(job_path)).name}"
        text = f"### {title}\n\n- 任务：`{job_path}`\n- 摘要：{summary}"
        return self.send_markdown(title, text)


def notify_job_failure(
    job_path: str | Path,
    exc: BaseException,
    *,
    traceback_text: str | None = None,
    enabled_override: bool | None = None,
) -> dict[str, Any] | None:
    """给 run_job.py 使用的失败通知快捷入口。"""
    if traceback_text is None:
        traceback_text = traceback.format_exc()
    notifier = DingTalkJobNotifier.from_config(enabled_override=enabled_override)
    return notifier.send_job_failed(job_path, exc, traceback_text=traceback_text)
