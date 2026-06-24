"""浏览器自动化登录兜底：iframe检测、NC滑块、短信验证循环。"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from . import havana

log = logging.getLogger("tb_login")

VERIFICATION_URL_MARKERS = (
    "/iv/", "normal_validate", "login_check", "havana_iv_token",
    "punish", "_____tmd_____", "nocaptcha", "captcha",
)


def is_verification_url(url: str) -> bool:
    lowered = (url or "").lower()
    return any(marker in lowered for marker in VERIFICATION_URL_MARKERS)


def is_seller_logged_in_url(url: str) -> bool:
    lowered = (url or "").lower()
    if not lowered or "login" in lowered or is_verification_url(lowered):
        return False
    return "taobao.com" in lowered or "tmall.com" in lowered or "alibaba.com" in lowered


def _browser_handle_sms(page: Any, sms_wait: int = 90) -> bool:
    try:
        try:
            from ..sms_helper import get_sms_code
        except ImportError:
            from sms_helper import get_sms_code

        send_btn = None
        for sel in ["css:#J_GetCode",
                    "xpath://button[contains(text(),'获取短信校验码')]",
                    "xpath://a[contains(text(),'获取') and contains(text(),'验证码')]",
                    "css:button[class*='send']", "css:button[class*='code']"]:
            try:
                ele = page.ele(sel, timeout=2)
                if ele and ele.states.is_displayed:
                    send_btn = ele
                    break
            except Exception:
                pass

        code_input = None
        for sel in ["css:#J_Phone_Checkcode", "css:input[name='_fm.v._0.ph']",
                    "css:input[placeholder*='验证码']"]:
            try:
                ele = page.ele(sel, timeout=2)
                if ele and ele.states.is_displayed:
                    code_input = ele
                    break
            except Exception:
                pass

        if not (send_btn and code_input):
            return False

        log.info("  浏览器验证: 检测到短信验证，点击获取验证码")
        try:
            send_btn.click()
        except Exception:
            try:
                send_btn.click(by_js=True)
            except Exception:
                pass

        code = get_sms_code(wait_seconds=sms_wait)
        if not code:
            log.warning("  浏览器验证: 未读取到短信验证码")
            return False

        code_input.clear()
        code_input.input(code)
        time.sleep(0.3)
        for sel in ["css:#submitBtn", "xpath://button[contains(text(),'确定')]",
                    "css:button[type='submit']", "xpath://button[contains(text(),'提交')]",
                    "xpath://button[contains(text(),'验证')]"]:
            try:
                btn = page.ele(sel, timeout=2)
                if btn and btn.states.is_displayed:
                    btn.click()
                    break
            except Exception:
                pass
        time.sleep(3)
        log.info("  浏览器验证: 已提交短信验证码")
        return True
    except Exception as exc:
        log.warning(f"  浏览器验证: 短信处理异常: {type(exc).__name__}: {exc}")
        return False


def browser_login_fallback() -> tuple[dict | None, str]:
    try:
        from DrissionPage import ChromiumPage, ChromiumOptions
    except ImportError:
        log.error("DrissionPage 未安装，无法使用浏览器降级方案")
        return None, "error:no_drissionpage"

    try:
        from ..auto_login.slider_helper import handle_nc_slider
    except ImportError:
        from auto_login.slider_helper import handle_nc_slider

    co = ChromiumOptions()
    co.auto_port(True)
    co.set_argument("--lang=zh-CN")
    co.set_argument("--disable-blink-features=AutomationControlled")
    co.set_pref("credentials_enable_service", False)
    co.set_pref("profile.password_manager_enabled", False)

    page = None
    try:
        page = ChromiumPage(addr_or_opts=co)

        _use_iframe = "mini_login.htm" in havana.HAVANA_LOGIN_URL
        ctx = page

        if _use_iframe:
            _parsed_qs = parse_qs(urlparse(havana.HAVANA_LOGIN_URL).query)
            _return_url = _parsed_qs.get("returnUrl", [""])[0]
            _real_login_page = _return_url if _return_url else havana.HAVANA_LOGIN_URL
            page.get(_real_login_page)
            time.sleep(4)
            try:
                ctx = page.get_frame("#alibaba-login-box")
            except Exception:
                try:
                    ctx = page.get_frame(0)
                except Exception:
                    log.warning("  无法进入 login iframe，回退到直接页面操作")
                    ctx = page
        else:
            page.get(havana.HAVANA_LOGIN_URL)
            time.sleep(3)

        # 切到密码登录 tab
        try:
            pwd_tab = ctx.ele("xpath://span[contains(text(),'密码登录')]", timeout=3)
            if pwd_tab:
                pwd_tab.click()
                time.sleep(0.5)
        except Exception:
            pass

        # 填写账号
        log.info("  填写账号密码...")
        login_input = None
        for sel in ["css:#fm-login-id", "css:input[name='loginId']",
                    "css:input[placeholder*='账号']", "css:input[placeholder*='手机']"]:
            try:
                login_input = ctx.ele(sel, timeout=3)
                if login_input:
                    break
            except Exception:
                pass
        if not login_input:
            page.get_screenshot(str(Path(__file__).parent / "debug_fallback.png"))
            log.error("  未找到账号框")
            return None, "error:no_login_input"
        login_input.clear()
        login_input.input(havana.LOGIN_ID)
        time.sleep(0.3)

        # 填写密码
        pwd_input = None
        for sel in ["css:#fm-login-password", "css:input[type='password']",
                    "css:input[name='password']", "css:input[placeholder*='密码']"]:
            try:
                pwd_input = ctx.ele(sel, timeout=3)
                if pwd_input:
                    break
            except Exception:
                pass
        if not pwd_input:
            page.get_screenshot(str(Path(__file__).parent / "debug_fallback.png"))
            log.error("  未找到密码框")
            return None, "error:no_password_input"
        pwd_input.clear()
        pwd_input.input(havana.PASSWORD)
        time.sleep(0.3)

        # 点击登录
        log.info("  点击登录...")
        login_btn = None
        for sel in ["css:#login-form button[type='submit']", "css:button[type='submit']",
                    "css:.btn-login", "css:.login-btn"]:
            try:
                login_btn = ctx.ele(sel, timeout=3)
                if login_btn:
                    break
            except Exception:
                pass
        if login_btn:
            login_btn.click()
        else:
            pwd_input.input("\n")
        time.sleep(3)

        # 处理协议弹窗
        for sel in ["xpath://button[text()='同意']", "xpath://div[text()='同意']",
                    "xpath://span[text()='同意']"]:
            try:
                ele = ctx.ele(sel, timeout=2)
                if ele and ele.states.is_displayed:
                    ele.click()
                    log.info("  已同意协议弹窗")
                    time.sleep(2)
                    break
            except Exception:
                pass

        # 验证处理循环
        for _round in range(8):
            if is_seller_logged_in_url(page.url):
                break
            for sel in ["xpath://button[text()='同意']", "xpath://span[text()='同意']"]:
                try:
                    ele = page.ele(sel, timeout=1)
                    if ele and ele.states.is_displayed:
                        ele.click()
                        time.sleep(1)
                except Exception:
                    pass

            if _browser_handle_sms(page, sms_wait=90):
                time.sleep(2)
            else:
                handle_nc_slider(ctx, max_retry=havana.SLIDER_RETRY, logger=log)
                time.sleep(3)

        # 等待最终跳转
        for _ in range(15):
            if is_seller_logged_in_url(page.url):
                log.info(f"  登录成功: {page.url}")
                break
            time.sleep(1)

        if is_seller_logged_in_url(page.url):
            browser_cookies = page.cookies()
            cookies_dict = {c["name"]: c["value"] for c in browser_cookies}
            page.quit()
            return cookies_dict, "success"

        status = "need_verify:iv" if is_verification_url(page.url) else "unknown"
        log.warning(f"  登录未完成（status={status}），当前 URL: {page.url[:80]}")
        try:
            page.get_screenshot(str(Path(__file__).parent / "debug.png"))
        except Exception:
            pass
        page.quit()
        return None, status

    except Exception as exc:
        log.error(f"  浏览器自动化异常: {exc}")
        if page:
            try:
                page.quit()
            except Exception:
                pass
        return None, f"error:{exc}"
