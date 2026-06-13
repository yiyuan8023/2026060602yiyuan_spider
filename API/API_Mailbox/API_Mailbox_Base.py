# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：Codex
- 创建时间：2026-06-13 19:26:00
- 最近修改：2026-06-13 19:26:28
- 文件用途：提供邮箱 IMAP 读取的基础能力，包括连接、最近邮件抓取、正文摘要提取和邮件筛选。
- 业务范围：适用于项目内所有依赖邮箱读取的能力，尤其是后续店铺登录验证码接入的底层数据获取。
- 依赖入口：使用标准库 dataclasses、email、imaplib、re 和 typing；复用 config.get_mailbox_config 与 extra.logger_.logger。
- 验收方式：修改后执行 py_compile；验证包导入、最近邮件读取和邮件筛选结果。
- 注意事项：禁止在日志中输出完整授权码、完整邮件正文或完整验证码；只保留必要摘要和状态信息。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from email import message_from_bytes, policy
from email.message import EmailMessage
from email.utils import parsedate_to_datetime
import imaplib
import re
from typing import Iterable, Optional

from config import get_mailbox_config
from extra.logger_ import logger

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - requirements.txt 已包含 beautifulsoup4
    BeautifulSoup = None


MAX_SUMMARY_LENGTH = 180
IMAP_CLIENT_ID = (
    "name",
    "yiyuan_spider",
    "version",
    "1.0",
    "vendor",
    "Codex",
    "support-email",
    "noreply@example.com",
)


class MailboxApiError(RuntimeError):
    """邮箱 IMAP 调用失败。"""


@dataclass
class MailboxMessage:
    """最近邮件的轻量摘要。"""

    uid: str
    sender: str
    subject: str
    sent_at: Optional[str]
    body_summary: str
    verification_code: Optional[str] = None
    body_text: str = field(default="", repr=False)

    def to_dict(self) -> dict:
        return {
            "uid": self.uid,
            "sender": self.sender,
            "subject": self.subject,
            "sent_at": self.sent_at,
            "body_summary": self.body_summary,
            "verification_code": self.verification_code,
        }


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def summarize_text(text: str, limit: int = MAX_SUMMARY_LENGTH) -> str:
    normalized = normalize_whitespace(text)
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def strip_html(html_text: str) -> str:
    if not html_text:
        return ""
    if BeautifulSoup is not None:
        return BeautifulSoup(html_text, "html.parser").get_text(" ", strip=True)
    return re.sub(r"<[^>]+>", " ", html_text)


def extract_message_text(message: EmailMessage) -> str:
    text_parts: list[str] = []
    html_parts: list[str] = []

    if message.is_multipart():
        for part in message.walk():
            if part.get_content_maintype() == "multipart":
                continue
            if part.get_content_disposition() == "attachment":
                continue
            content_type = part.get_content_type()
            content = part.get_content()
            if not isinstance(content, str):
                continue
            if content_type == "text/plain":
                text_parts.append(content)
            elif content_type == "text/html":
                html_parts.append(content)
    else:
        content = message.get_content()
        if isinstance(content, str):
            if message.get_content_type() == "text/html":
                html_parts.append(content)
            else:
                text_parts.append(content)

    if text_parts:
        return normalize_whitespace("\n".join(text_parts))
    if html_parts:
        return normalize_whitespace(strip_html("\n".join(html_parts)))
    return ""


def format_message_datetime(raw_value: Optional[str]) -> Optional[str]:
    if not raw_value:
        return None
    try:
        parsed = parsedate_to_datetime(raw_value)
    except (TypeError, ValueError, IndexError):
        return raw_value
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone()
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


class MailboxBaseApi:
    """邮箱 IMAP 基础 API。"""

    def __init__(self, mailbox_config: Optional[dict] = None):
        self.mailbox_config = mailbox_config or get_mailbox_config()

    @staticmethod
    def _send_imap_id(client) -> None:
        """向部分邮箱服务声明客户端身份，兼容 163 的 Unsafe Login 限制。"""
        imaplib.Commands["ID"] = ("AUTH",)
        id_payload = '("' + '" "'.join(IMAP_CLIENT_ID) + '")'
        status, _ = client._simple_command("ID", id_payload)
        if status != "OK":
            logger.warning("IMAP ID 声明未成功，后续如遇 Unsafe Login 可能无法读取邮件。")

    def connect(self):
        """建立 IMAP 连接并完成登录。"""
        host = self.mailbox_config["host"]
        port = self.mailbox_config["port"]
        timeout = self.mailbox_config["timeout"]

        if self.mailbox_config["use_ssl"]:
            client = imaplib.IMAP4_SSL(host=host, port=port, timeout=timeout)
        else:
            client = imaplib.IMAP4(host=host, port=port, timeout=timeout)

        try:
            client.login(
                self.mailbox_config["username"],
                self.mailbox_config["password"],
            )
        except imaplib.IMAP4.error as exc:
            raise MailboxApiError(f"邮箱登录失败: {exc}") from exc

        self._send_imap_id(client)
        return client

    def fetch_recent_messages(self, limit: int = 20, mailbox: Optional[str] = None) -> list[MailboxMessage]:
        """读取指定文件夹最近 N 封邮件摘要。"""
        if limit <= 0:
            raise ValueError("limit 必须大于 0")

        folder_name = mailbox or self.mailbox_config["folder"]
        logger.info(f"开始读取邮箱最近邮件，folder={folder_name}，limit={limit}")

        client = self.connect()
        try:
            status, _ = client.select(folder_name, readonly=True)
            if status != "OK":
                raise MailboxApiError(
                    f"邮箱文件夹打开失败: {folder_name}。"
                    "如果是 163 邮箱并提示 Unsafe Login，请先确认已开启 IMAP，"
                    "并完成网易客户端安全验证。"
                )

            status, data = client.uid("search", None, "ALL")
            if status != "OK":
                raise MailboxApiError("邮箱 UID 搜索失败")

            uid_list = data[0].split() if data and data[0] else []
            selected_uids = list(reversed(uid_list[-limit:]))
            messages: list[MailboxMessage] = []

            for raw_uid in selected_uids:
                status, message_data = client.uid("fetch", raw_uid, "(BODY.PEEK[])")
                if status != "OK":
                    logger.warning("单封邮件抓取失败，已跳过。")
                    continue

                raw_message = None
                for item in message_data or []:
                    if isinstance(item, tuple) and len(item) >= 2:
                        raw_message = item[1]
                        break
                if not raw_message:
                    continue

                message = message_from_bytes(raw_message, policy=policy.default)
                body_text = extract_message_text(message)
                messages.append(
                    MailboxMessage(
                        uid=raw_uid.decode() if isinstance(raw_uid, bytes) else str(raw_uid),
                        sender=str(message.get("from", "")).strip(),
                        subject=str(message.get("subject", "")).strip(),
                        sent_at=format_message_datetime(message.get("date")),
                        body_summary=summarize_text(body_text),
                        body_text=body_text,
                    )
                )

            logger.info(f"邮箱读取完成，共获取 {len(messages)} 封摘要邮件。")
            return messages
        finally:
            try:
                client.logout()
            except Exception:  # noqa: BLE001
                pass

    @staticmethod
    def filter_messages(
        messages: Iterable[MailboxMessage],
        sender_keyword: Optional[str] = None,
        subject_keyword: Optional[str] = None,
    ) -> list[MailboxMessage]:
        """按发件人或标题关键词筛选邮件。"""
        filtered: list[MailboxMessage] = []
        sender_keyword_lower = sender_keyword.lower() if sender_keyword else None
        subject_keyword_lower = subject_keyword.lower() if subject_keyword else None

        for message in messages:
            if sender_keyword_lower and sender_keyword_lower not in message.sender.lower():
                continue
            if subject_keyword_lower and subject_keyword_lower not in message.subject.lower():
                continue
            filtered.append(message)
        return filtered
