# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：Codex
- 创建时间：2026-06-13 19:26:00
- 最近修改：2026-06-13 20:11:17
- 文件用途：暴露邮箱 IMAP 读取和验证码提取 API 包的统一导出入口。
- 业务范围：适用于店铺登录、短信验证码提取、邮箱摘要预览等需要读取 163 邮箱的项目内模块。
- 依赖入口：使用 API_Mailbox_Base、API_Mailbox_VerificationCode 两个模块中的公共类和能力。
- 验收方式：修改后执行 py_compile，并验证 API.API_Mailbox 包导入成功。
- 注意事项：不要在包入口硬编码真实邮箱账号或授权码；敏感配置统一走本地配置或环境变量。
"""

from API.API_Mailbox.API_Mailbox_Base import MailboxApiError, MailboxBaseApi, MailboxMessage
from API.API_Mailbox.API_Mailbox_VerificationCode import (
    MailboxVerificationCodeApi,
    PasswordExtractResult,
    VerificationCodeMatch,
    VerificationCodeExtractResult,
    extract_password_from_message,
    extract_password_from_text,
    extract_source,
    extract_verification_code_from_message,
    extract_verification_code_from_text,
)

__all__ = [
    "MailboxApiError",
    "MailboxBaseApi",
    "MailboxMessage",
    "MailboxVerificationCodeApi",
    "PasswordExtractResult",
    "VerificationCodeMatch",
    "VerificationCodeExtractResult",
    "extract_password_from_message",
    "extract_password_from_text",
    "extract_source",
    "extract_verification_code_from_message",
    "extract_verification_code_from_text",
]
