#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
短信验证码自动获取模块

通过163邮箱IMAP读取转发的淘宝短信验证码。
依赖: 原始项目 F:\05ai_project\2026060602yiyuan_spider 中的 API_Mailbox 模块。
"""

import sys
import time
import logging
from pathlib import Path

log = logging.getLogger("tb_login")

# 将原始项目加入 sys.path 以复用邮箱 API
_SPIDER_PROJECT = Path(r"F:\05ai_project\2026060602yiyuan_spider")
if str(_SPIDER_PROJECT) not in sys.path:
    sys.path.insert(0, str(_SPIDER_PROJECT))


def get_sms_code(
    wait_seconds: int = 60,
    poll_interval: int = 5,
    sender_keyword: str = None,
    subject_keyword: str = "验证码",
) -> str | None:
    """
    等待并获取最新的淘宝短信验证码。

    流程:
    1. 记录当前时间作为基准
    2. 循环轮询邮箱，查找基准时间之后收到的验证码邮件
    3. 找到则返回验证码字符串，超时返回 None

    Args:
        wait_seconds: 最长等待时间(秒)
        poll_interval: 轮询间隔(秒)
        sender_keyword: 发件人过滤关键词 (如 "taobao", "阿里")
        subject_keyword: 主题过滤关键词 (如 "验证码")

    Returns:
        验证码字符串，或 None
    """
    try:
        from API.API_Mailbox import MailboxVerificationCodeApi
    except ImportError as e:
        log.error(f"  无法导入邮箱 API: {e}")
        log.error(f"  请确认 {_SPIDER_PROJECT} 路径正确且依赖已安装")
        return None

    log.info(f"  等待短信验证码 (最多 {wait_seconds}s, 每 {poll_interval}s 检查一次)...")
    start_time = time.time()
    last_seen_uid = None

    # 先获取当前最新邮件的 UID 作为基准（排除旧验证码）
    try:
        api = MailboxVerificationCodeApi()
        baseline = api.find_latest_verification_code(
            limit=5,
            sender_keyword=sender_keyword,
            subject_keyword=subject_keyword,
        )
        if baseline:
            last_seen_uid = baseline.uid
            log.info(f"  基准邮件 UID: {last_seen_uid} (忽略此前的验证码)")
    except Exception as exc:
        log.warning(f"  获取基准邮件失败: {exc}")

    # 轮询等待新验证码
    while time.time() - start_time < wait_seconds:
        time.sleep(poll_interval)
        elapsed = int(time.time() - start_time)
        log.info(f"  检查邮箱... ({elapsed}s/{wait_seconds}s)")

        try:
            api = MailboxVerificationCodeApi()
            result = api.find_latest_verification_code(
                limit=10,
                sender_keyword=sender_keyword,
                subject_keyword=subject_keyword,
            )
            if result and result.uid != last_seen_uid:
                log.info(f"  收到验证码: {result.code} (来自: {result.sender})")
                return result.code
        except Exception as exc:
            log.warning(f"  邮箱查询异常: {exc}")

    log.warning(f"  等待 {wait_seconds}s 未收到验证码")
    return None


def get_sms_code_immediate(
    sender_keyword: str = None,
    subject_keyword: str = "验证码",
) -> str | None:
    """
    立即获取最新的验证码（不等待，直接取最新一封）。
    适用于验证码已经发送的场景。
    """
    try:
        from API.API_Mailbox import MailboxVerificationCodeApi
    except ImportError as e:
        log.error(f"  无法导入邮箱 API: {e}")
        return None

    try:
        api = MailboxVerificationCodeApi()
        result = api.find_latest_verification_code(
            limit=10,
            sender_keyword=sender_keyword,
            subject_keyword=subject_keyword,
        )
        if result:
            log.info(f"  最新验证码: {result.code} (来自: {result.sender}, 时间: {result.sent_at})")
            return result.code
    except Exception as exc:
        log.warning(f"  邮箱查询异常: {exc}")

    return None
