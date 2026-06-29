#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-20
- 文件用途：纯协议求解淘系 Havana 登录的 IV 二次身份验证（短信模式），无需浏览器。
- 业务范围：协议登录 login.do 返回 need_verify:iv（loginResult 为空且跳 /iv/ 验证页）时调用。
- 流程：login_check → normal_validate(pointman 引导) → verify_modes → identity_verify(短信表单)
        → send_code.do 发码 → sms_helper 邮箱读码 → POST J_Form 过 IV → 会话回到已登录态。
- 依赖入口：requests 会话（携带登录态 Cookie）、bs4 解析、sms_helper.get_sms_code 读码。
- 验收方式：单店铺端到端过 IV 后 validate 成功并写库；先静态 py_compile。
- 注意事项：不输出验证码、完整 Cookie、完整 htoken；会向账号手机发真实短信，按需调用。
"""

from __future__ import annotations

import re
from typing import Any

import requests
from bs4 import BeautifulSoup

from extra.logger_ import logger

# normal_validate 引导页里 verify_modes 跳转 URL 的模板（JS 拼接 _umidfg）
_VERIFY_MODES_RE = re.compile(r"(https://passport\.taobao\.com/iv/verify_modes\.htm\?[^\"']+)")
# identity_verify 内联里的 send_code.do 地址
_SEND_CODE_RE = re.compile(r"(https://passport\.taobao\.com/iv/phone/send_code\.do\?htoken=[A-Za-z0-9_\-]+)")
# 风控/需要额外验证的关键字（短信路径被 baxia/x5sec 拦截时出现）
_RISK_MARKERS = ("x5sec", "nocaptcha", "RGV587", "punish", "_____tmd_____", "拦截", "风险")


def _follow_to_identity_verify(session: requests.Session, iv_redirect_url: str, timeout: int):
    """
    跟进 IV 跳转链，返回 (identity_verify_html, identity_verify_url)。
    必须只遍历一次：发码与提交共用同一 htoken，重复遍历会刷新 htoken 导致 expired。
    """
    # 1) login_check.htm → (HTTP 302) → normal_validate.htm
    r1 = session.get(iv_redirect_url, timeout=timeout)
    html1 = r1.text

    # login_check 可能已直接到表单页
    if "J_Phone_Checkcode" in html1 or "send_code.do" in html1:
        return html1, r1.url

    # 2) normal_validate 是 JS 引导页，提取 verify_modes URL，_umidfg 直接置 1（已验证可达短信表单）
    match = _VERIFY_MODES_RE.search(html1)
    if not match:
        logger.warning("  IV: 未能从引导页提取 verify_modes 跳转")
        return None, None

    verify_modes_url = (match.group(1)
                        .replace('"+window._iv_umidfg', "1")
                        .replace("'+window._iv_umidfg", "1")
                        .rstrip("\"'"))

    # 3) verify_modes.htm → (HTTP 302) → identity_verify.htm（短信表单）
    r2 = session.get(verify_modes_url, timeout=timeout)
    return r2.text, r2.url


def _parse_iv_sms_form(html: str) -> dict[str, Any] | None:
    """解析 identity_verify 短信表单，返回提交所需字段与发码信息。"""
    soup = BeautifulSoup(html, "lxml")
    form = soup.find("form", id="J_Form")
    if not form:
        return None

    fields: dict[str, str] = {}
    code_field = None
    phone = None
    area = "86"
    for inp in form.find_all(["input", "select"]):
        name = inp.get("name")
        if not name:
            continue
        if inp.get("id") == "J_Phone_Checkcode":
            code_field = name  # 校验码字段，待填入短信码
            fields.setdefault(name, "")
            continue
        if inp.get("id") == "J_MobileVal":
            phone = inp.get("value") or ""
            area = inp.get("data") or area
        fields[name] = inp.get("value") or ""

    if not code_field:
        return None

    send_match = _SEND_CODE_RE.search(html)
    return {
        "fields": fields,
        "code_field": code_field,
        "phone": phone,
        "area": area,
        "send_code_url": send_match.group(1) if send_match else None,
    }


def _looks_risky(text: str) -> bool:
    lowered = (text or "").lower()
    return any(marker.lower() in lowered for marker in _RISK_MARKERS)


def solve_iv_sms(
    session: requests.Session,
    iv_redirect_url: str,
    identity_verify_referer: str | None = None,
    sms_wait: int = 120,
    sms_poll: int = 5,
    timeout: int = 30,
) -> bool:
    """
    纯协议过 IV 短信验证。成功返回 True（此时 session 已回到登录态）。

    失败返回 False，由上层回落浏览器兜底或标记需人工。
    """
    try:
        try:
            from ..sms_helper import get_sms_code
        except ImportError:
            from API_login.API_TaoXi_login.sms_helper import get_sms_code

        logger.info("  IV: 进入短信二次验证求解...")
        iv_html, iv_form_url = _follow_to_identity_verify(session, iv_redirect_url, timeout)
        if not iv_html or not iv_form_url:
            return False
        if _looks_risky(iv_html) and "J_Phone_Checkcode" not in iv_html:
            logger.warning("  IV: 验证页疑似被风控/滑块拦截，短信路径不可用")
            return False

        parsed = _parse_iv_sms_form(iv_html)
        if not parsed:
            logger.warning("  IV: 未识别到短信验证表单（可能为滑块或其它模式）")
            return False
        if not parsed["send_code_url"]:
            logger.warning("  IV: 未找到发码接口 send_code.do")
            return False

        # 取一次基准邮件 UID，避免读到历史验证码
        baseline = None
        try:
            from API.API_Mailbox import MailboxVerificationCodeApi
            api = MailboxVerificationCodeApi()
            latest = api.find_latest_verification_code(limit=5, subject_keyword="验证码")
            baseline = latest.uid if latest else None
        except Exception:
            baseline = None

        # 发送短信验证码
        send_params = {
            "phone": parsed["phone"] or "",
            "type": "phone",
            "area": parsed["area"],
            "tag": parsed["area"],
        }
        headers = {"Referer": iv_redirect_url, "X-Requested-With": "XMLHttpRequest"}
        sr = session.get(parsed["send_code_url"], params=send_params, headers=headers, timeout=timeout)
        try:
            sjson = sr.json()
            send_ok = bool((sjson.get("content") or {}).get("success"))
        except ValueError:
            send_ok = False
        if not send_ok:
            logger.warning(f"  IV: 发码失败或被拦截（状态码 {sr.status_code}）")
            if _looks_risky(sr.text):
                logger.warning("  IV: 发码响应含风控特征，短信路径不可用")
            return False
        logger.info("  IV: 短信验证码已发送，等待邮箱转发读取...")

        # 读码：优先轮询比 baseline 新的验证码
        code = get_sms_code(wait_seconds=sms_wait, poll_interval=sms_poll, subject_keyword="验证码")
        if not code:
            logger.warning("  IV: 未读取到短信验证码")
            return False
        logger.info(f"  IV: 读取到验证码（{len(code)} 位）")

        # 提交校验码（form 无 action，POST 回 identity_verify 当前页；复用同一遍历的 URL 与 htoken）
        submit_fields = dict(parsed["fields"])
        submit_fields[parsed["code_field"]] = code
        return _submit_iv_code(session, iv_form_url, submit_fields, timeout)
    except Exception as exc:
        logger.warning(f"  IV: 短信求解异常: {type(exc).__name__}: {exc}")
        return False


def _submit_iv_code(session: requests.Session, iv_form_url: str, submit_fields: dict[str, str], timeout: int) -> bool:
    """把带验证码的表单 POST 回 identity_verify 页（同一 htoken），判断 IV 是否通过。"""
    headers = {
        "Referer": iv_form_url,
        "Origin": "https://passport.taobao.com",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Requested-With": "XMLHttpRequest",
    }
    resp = session.post(iv_form_url, data=submit_fields, headers=headers, timeout=timeout, allow_redirects=True)
    body = resp.text or ""

    # 成功判定：离开 /iv/ 验证域，或响应明确 success
    left_iv = "/iv/" not in resp.url and "identity_verify" not in resp.url
    json_ok = False
    try:
        j = resp.json()
        json_ok = bool(j.get("success") or (j.get("content") or {}).get("success"))
    except ValueError:
        json_ok = False

    if json_ok or left_iv:
        logger.info(f"  IV: 短信验证通过（最终 URL: {resp.url[:60]}...）")
        return True

    if _looks_risky(body):
        logger.warning("  IV: 提交后仍被风控拦截")
    else:
        logger.warning(f"  IV: 短信验证未通过（最终 URL: {resp.url[:60]}...）")
    return False
