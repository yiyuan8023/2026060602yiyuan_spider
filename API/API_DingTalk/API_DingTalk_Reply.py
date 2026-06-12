# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一贯
- 创建时间：2026-06-11 06:29:55
- 最近修改：2026-06-11 06:29:55
- 文件用途：封装钉钉企业内部应用机器人 Stream 模式接收消息、保存最近会话和 sessionWebhook 回复能力。
- 业务范围：适用于群内 @机器人 后的自动回复、验证码提取、最近会话保存和临时 sessionWebhook 调试回复。
- 依赖入口：运行时使用 dingtalk_stream；静态导入 API_DingTalk_Base、extra.logger_、json、re 和 pathlib。
- 验收方式：修改后执行 py_compile；未配置真实 AppKey/AppSecret 时只做模块导入探针，真实连接需在钉钉群内 @机器人验证。
- 注意事项：sessionWebhook 会过期，只适合上下文回复，不作为长期任务告警通道；状态文件包含临时 Webhook，必须保持忽略。
"""

import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Any

from API.API_DingTalk.API_DingTalk_Base import (
    DingTalkConfigError,
    ensure_state_dir,
    get_config_value,
    load_dingtalk_section,
    require_config_value,
)
from extra.logger_ import logger


LAST_MESSAGE_PATH = ensure_state_dir() / "last_dingtalk_message.json"
LATEST_CODE_PATH = ensure_state_dir() / "latest_dingtalk_verification_code.json"

CODE_PATTERNS = (
    re.compile(r"(?:验证码|校验码|动态码|登录码|code)\D{0,12}(\d{4,8})", re.IGNORECASE),
    re.compile(r"(\d{4,8})\D{0,12}(?:验证码|校验码|动态码|登录码|code)", re.IGNORECASE),
)
PLATFORM_PATTERN = re.compile(r"【([^】]{1,30})】")
VALID_MINUTES_PATTERN = re.compile(r"(\d{1,3})\s*分钟内有效")
FORWARDED_FROM_PATTERN = re.compile(r"转发自[:：]\s*(.+)")
SMS_TIME_PATTERN = re.compile(r"时间[:：]\s*([0-9:\-\s/]+)")


@dataclass(frozen=True)
class VerificationCode:
    """短信验证码解析结果。"""

    code: str
    masked_code: str
    platform: str
    valid_minutes: int | None
    sms_time: str
    forwarded_from: str
    raw_text: str
    received_at: int


def normalize_text(parts: Iterable[str] | None) -> str:
    """把钉钉 SDK 提取出的文本片段整理成字符串。"""
    if not parts:
        return ""
    return "\n".join(part.strip() for part in parts if part and part.strip()).strip()


def mask_code(code: str) -> str:
    """脱敏验证码。"""
    if len(code) <= 3:
        return "*" * len(code)
    return f"{code[:3]}{'*' * (len(code) - 3)}"


def _first_match(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def extract_verification_code(text: str) -> VerificationCode | None:
    """从群消息中提取短信验证码。"""
    normalized = (text or "").strip()
    if not normalized:
        return None

    code = ""
    for pattern in CODE_PATTERNS:
        match = pattern.search(normalized)
        if match:
            code = match.group(1)
            break

    if not code:
        return None

    valid_minutes_text = _first_match(VALID_MINUTES_PATTERN, normalized)
    valid_minutes = int(valid_minutes_text) if valid_minutes_text else None
    return VerificationCode(
        code=code,
        masked_code=mask_code(code),
        platform=_first_match(PLATFORM_PATTERN, normalized),
        valid_minutes=valid_minutes,
        sms_time=_first_match(SMS_TIME_PATTERN, normalized),
        forwarded_from=_first_match(FORWARDED_FROM_PATTERN, normalized),
        raw_text=normalized,
        received_at=int(time.time() * 1000),
    )


def save_json(path: Path, payload: dict[str, Any]) -> None:
    """保存钉钉运行状态。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def save_verification_code(result: VerificationCode, output_path: Path = LATEST_CODE_PATH) -> None:
    """保存最近一次验证码解析结果。"""
    save_json(output_path, asdict(result))


def save_last_message(incoming: Any, text: str, output_path: Path = LAST_MESSAGE_PATH) -> None:
    """保存最近一次机器人收到的消息上下文。"""
    payload = {
        "conversation_id": getattr(incoming, "conversation_id", ""),
        "conversation_type": getattr(incoming, "conversation_type", ""),
        "conversation_title": getattr(incoming, "conversation_title", ""),
        "sender_nick": getattr(incoming, "sender_nick", ""),
        "sender_staff_id": getattr(incoming, "sender_staff_id", ""),
        "session_webhook": getattr(incoming, "session_webhook", ""),
        "session_webhook_expired_time": getattr(incoming, "session_webhook_expired_time", ""),
        "message_type": getattr(incoming, "message_type", ""),
        "text": text,
        "saved_at": int(time.time() * 1000),
    }
    save_json(output_path, payload)


class DingTalkStreamReplyBot:
    """钉钉 Stream 机器人。"""

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        *,
        reply_prefix: str | None = None,
    ) -> None:
        section = load_dingtalk_section()
        self.client_id = require_config_value(
            client_id or get_config_value("DINGTALK_CLIENT_ID", "client_id", section=section),
            "DINGTALK_CLIENT_ID / dingtalk.client_id",
        )
        self.client_secret = require_config_value(
            client_secret or get_config_value("DINGTALK_CLIENT_SECRET", "client_secret", section=section),
            "DINGTALK_CLIENT_SECRET / dingtalk.client_secret",
        )
        self.reply_prefix = reply_prefix or get_config_value(
            "DINGTALK_REPLY_PREFIX",
            "reply_prefix",
            "收到：",
            section=section,
        )

    def start_forever(self) -> None:
        """启动 Stream 长连接并注册机器人消息回调。"""
        try:
            import dingtalk_stream
        except ImportError as exc:
            raise DingTalkConfigError("缺少依赖 dingtalk-stream，请先安装 requirements.txt") from exc

        reply_prefix = self.reply_prefix

        class _Handler(dingtalk_stream.ChatbotHandler):
            async def process(self, callback_message: Any):  # noqa: ANN001
                incoming = dingtalk_stream.ChatbotMessage.from_dict(callback_message.data)
                text = normalize_text(self.extract_text_from_incoming_message(incoming))
                logger.info(
                    f"钉钉机器人收到消息：type={incoming.message_type} "
                    f"sender={incoming.sender_nick} conversation={incoming.conversation_title} "
                    f"conversation_id={incoming.conversation_id} text_length={len(text)}"
                )
                save_last_message(incoming, text)

                if not incoming.session_webhook:
                    logger.warning("钉钉消息缺少sessionWebhook，无法回复")
                    return dingtalk_stream.AckMessage.STATUS_OK, "OK"

                if incoming.message_type != "text" or not text:
                    self.reply_text("我已收到消息，但当前只处理文本。", incoming)
                    return dingtalk_stream.AckMessage.STATUS_OK, "OK"

                verification_code = extract_verification_code(text)
                if verification_code:
                    save_verification_code(verification_code)
                    reply = f"已提取验证码：{verification_code.masked_code}"
                    if verification_code.platform:
                        reply += f"，平台：{verification_code.platform}"
                    self.reply_text(reply, incoming)
                    return dingtalk_stream.AckMessage.STATUS_OK, "OK"

                self.reply_text(f"{reply_prefix}{text}", incoming)
                return dingtalk_stream.AckMessage.STATUS_OK, "OK"

        credential = dingtalk_stream.Credential(self.client_id, self.client_secret)
        client = dingtalk_stream.DingTalkStreamClient(credential)
        client.register_callback_handler(dingtalk_stream.ChatbotMessage.TOPIC, _Handler())
        logger.info("钉钉Stream机器人启动")
        client.start_forever()
