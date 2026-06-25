"""浏览器自动化登录兜底：iframe检测、NC滑块、短信验证循环。"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from . import havana
from extra.logger_ import logger

VERIFICATION_URL_MARKERS = (
    "/iv/", "normal_validate", "login_check", "havana_iv_token",
    "punish", "_____tmd_____", "nocaptcha", "captcha",
)


def _read_input_value(ctx: Any, ele: Any) -> str:
    """读输入框的真实 value（property，而非 HTML attribute）。动态输入下 attr('value') 恒为 None。"""
    try:
        return ctx.run_js("return arguments[0].value;", ele) or ""
    except Exception:
        return ""


def _js_set_value(ctx: Any, ele: Any, value: str) -> None:
    """JS 兜底赋值并派发 input/change 事件，绕过受控组件/拦截导致的 .input() 不生效。"""
    try:
        ctx.run_js(
            "arguments[0].value=arguments[1];"
            "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
            "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
            ele, value,
        )
    except Exception as exc:
        logger.warning(f"  JS 兜底赋值失败: {type(exc).__name__}: {exc}")


def is_verification_url(url: str) -> bool:
    lowered = (url or "").lower()
    return any(marker in lowered for marker in VERIFICATION_URL_MARKERS)


def is_seller_logged_in_url(url: str) -> bool:
    lowered = (url or "").lower()
    if not lowered or "login" in lowered or is_verification_url(lowered):
        return False
    return "taobao.com" in lowered or "tmall.com" in lowered or "alibaba.com" in lowered


SMS_SEND_SELECTORS = [
    "css:#J_GetCode", "css:.getcheckcode",
    "xpath://*[contains(text(),'点击获取验证码')]",
    "xpath://button[contains(text(),'获取') and contains(text(),'验证码')]",
    "xpath://button[contains(text(),'获取') and contains(text(),'校验码')]",
    "xpath://a[contains(text(),'获取') and contains(text(),'验证码')]",
    "xpath://span[contains(text(),'获取') and contains(text(),'验证码')]",
    "css:.send-btn", "css:[class*='getCode']", "css:[class*='sendCode']",
    "css:button[class*='send']", "css:button[class*='code']",
]
SMS_CODE_INPUT_SELECTORS = [
    "css:#J_Checkcode", "css:#J_Phone_Checkcode", "css:input[name='_fm.v._0.ph']",
    "css:input.ui-input-checkcode", "css:input[name='checkCode']",
    "css:input[placeholder*='6位']", "css:input[placeholder*='验证码']",
    "css:input[placeholder*='校验码']", "css:input[id*='checkcode' i]",
]
SMS_SUBMIT_SELECTORS = [
    "css:#submitBtn", "xpath://button[contains(text(),'确定')]",
    "xpath://button[contains(text(),'确认')]", "xpath://button[contains(text(),'提交')]",
    "xpath://button[contains(text(),'验证')]", "css:button[type='submit']",
]


_FRAME_SKIP_MARKERS = ("g.alicdn.com", "xstore", "1688.com", "xdomain", "aplus")


def _all_contexts(page: Any, max_depth: int = 4) -> list[Any]:
    """主页面 + 递归所有 iframe 上下文。

    IV 短信验证框嵌在 login.jhtml iframe 内部再一层（passport.taobao.com/iv），
    只遍历顶层 iframe 会漏掉它，导致找不到“获取验证码”按钮。
    """
    ctxs: list[Any] = []

    def _collect(ctx: Any, depth: int) -> None:
        ctxs.append(ctx)
        if depth >= max_depth:
            return
        try:
            for ifr in ctx.eles("tag:iframe"):
                src = ifr.attr("src") or ""
                if any(marker in src for marker in _FRAME_SKIP_MARKERS):
                    continue
                try:
                    fr = ctx.get_frame(ifr)
                    if fr:
                        _collect(fr, depth + 1)
                except Exception:
                    continue
        except Exception:
            pass

    _collect(page, 0)
    return ctxs


def _find_in_contexts(ctxs: list[Any], selectors: list[str], timeout: int = 1):
    """在多个上下文中按选择器找首个可见元素，返回 (ctx, element, selector)。"""
    for ctx in ctxs:
        for sel in selectors:
            try:
                ele = ctx.ele(sel, timeout=timeout)
                if ele and ele.states.is_displayed:
                    return ctx, ele, sel
            except Exception:
                continue
    return None, None, None


def _dump_verify_ui(ctxs: list[Any]) -> None:
    """在含“验证码”文本但元素没命中的 frame 上，打印按钮/输入框，便于补全选择器。"""
    for i, ctx in enumerate(ctxs):
        try:
            txt = ctx.run_js("return document.body.innerText;") or ""
        except Exception:
            txt = ""
        if "验证码" not in txt and "校验码" not in txt:
            continue
        logger.info(f"  [诊断] frame#{i} 含验证码文本，候选控件如下：")
        try:
            for b in ctx.eles("tag:button")[:10]:
                logger.info(f"    button text={(b.text or '')[:20]!r} class={(b.attr('class') or '')[:40]!r}")
            for a in ctx.eles("tag:a")[:10]:
                t = (a.text or "").strip()
                if t:
                    logger.info(f"    a text={t[:20]!r} id={a.attr('id')!r}")
            for ip in ctx.eles("tag:input")[:10]:
                logger.info(f"    input id={ip.attr('id')!r} name={ip.attr('name')!r} ph={ip.attr('placeholder')!r}")
        except Exception:
            pass


def _send_btn_in_cooldown(btn: Any) -> bool:
    """“获取验证码”按钮点击后进入 ~60s 倒计时（文本含数字/秒/重新/重试），此时不可重复点。"""
    try:
        txt = (btn.text or "").strip()
    except Exception:
        return False
    if not txt:
        return False
    if "重新" in txt or "秒" in txt or "重试" in txt or "后" in txt:
        return True
    return any(ch.isdigit() for ch in txt)


def _wait_send_clickable(page: Any, timeout: int = 65):
    """等到“获取验证码”按钮脱离倒计时可再次点击，返回 (ctxs, btn, selector)。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        ctxs = _all_contexts(page)
        _, btn, sel = _find_in_contexts(ctxs, SMS_SEND_SELECTORS)
        if not btn:
            return ctxs, None, None
        if not _send_btn_in_cooldown(btn):
            return ctxs, btn, sel
        time.sleep(2)
    ctxs = _all_contexts(page)
    _, btn, sel = _find_in_contexts(ctxs, SMS_SEND_SELECTORS)
    return ctxs, btn, sel


def _sms_verify_passed(page: Any) -> bool:
    """提交后判断短信验证是否通过：已跳离登录页，或验证码输入框已消失。"""
    if is_seller_logged_in_url(page.url):
        return True
    _, code_input, _ = _find_in_contexts(_all_contexts(page), SMS_CODE_INPUT_SELECTORS)
    return code_input is None


def _browser_handle_sms(page: Any, sms_wait: int = 55, max_attempts: int = 4) -> bool:
    """处理 IV 短信验证。验证码 60s 失效：单次轮询窗口 <60s，取码后立即提交；
    未通过则等按钮倒计时结束、重新获取全新验证码再试。"""
    try:
        try:
            from ..sms_helper import get_sms_code
        except ImportError:
            from sms_helper import get_sms_code

        ctxs = _all_contexts(page)
        _, send_btn, ssel = _find_in_contexts(ctxs, SMS_SEND_SELECTORS)
        _, code_input, csel = _find_in_contexts(ctxs, SMS_CODE_INPUT_SELECTORS)
        if not (send_btn and code_input):
            _dump_verify_ui(ctxs)
            return False

        logger.info(f"  浏览器验证: 检测到短信验证(send={ssel}, input={csel})")
        # 单次轮询窗口压到 60s 以内，避免坐等过期码
        wait_window = min(int(sms_wait or 55), 55)

        for attempt in range(1, max_attempts + 1):
            # 等按钮可点（首轮即可点；重试时等满倒计时拿全新码）
            ctxs, send_btn, ssel = _wait_send_clickable(page)
            if not send_btn:
                logger.warning("  浏览器验证: 获取验证码按钮丢失")
                return False

            logger.info(f"  浏览器验证: 第 {attempt}/{max_attempts} 次点击获取验证码")
            try:
                send_btn.click()
            except Exception:
                try:
                    send_btn.click(by_js=True)
                except Exception:
                    pass
            click_ts = time.time()

            code = get_sms_code(wait_seconds=wait_window)
            if not code:
                logger.warning("  浏览器验证: 本轮未读到验证码，重试（确认短信已转发到邮箱）")
                continue

            elapsed = time.time() - click_ts
            if elapsed > 58:
                logger.warning(f"  浏览器验证: 读码耗时 {elapsed:.0f}s 超 60s，码已可能失效，重新获取")
                continue

            # 立即填入并提交（重新定位输入框，防 iframe 重渲染导致旧引用失效）
            _, code_input, _ = _find_in_contexts(_all_contexts(page), SMS_CODE_INPUT_SELECTORS)
            if not code_input:
                logger.warning("  浏览器验证: 验证码输入框丢失，重试")
                continue
            try:
                code_input.clear()
                code_input.input(code)
            except Exception:
                logger.warning("  浏览器验证: 填入验证码失败，重试")
                continue
            time.sleep(0.3)
            _, submit_btn, _ = _find_in_contexts(_all_contexts(page), SMS_SUBMIT_SELECTORS)
            if submit_btn:
                try:
                    submit_btn.click()
                except Exception:
                    try:
                        submit_btn.click(by_js=True)
                    except Exception:
                        pass
            time.sleep(3)
            logger.info(f"  浏览器验证: 已提交验证码（读码耗时 {elapsed:.0f}s）")

            if _sms_verify_passed(page):
                logger.info("  浏览器验证: 短信验证通过")
                return True
            logger.warning("  浏览器验证: 提交后仍在验证页（码失效/错误/还有下一道），重试")

        return False
    except Exception as exc:
        logger.warning(f"  浏览器验证: 短信处理异常: {type(exc).__name__}: {exc}")
        return False


def browser_login_fallback() -> tuple[dict | None, str]:
    try:
        from DrissionPage import ChromiumPage, ChromiumOptions
    except ImportError:
        logger.error("DrissionPage 未安装，无法使用浏览器降级方案")
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
            _app_name = _parsed_qs.get("appName", [""])[0]
            _real_login_page = _return_url if _return_url else havana.HAVANA_LOGIN_URL
            page.get(_real_login_page)
            time.sleep(4)

            # 在主页面上切换登录tab（tab在主页面，不在iframe里）
            if _app_name == "taobao":
                # DChain淘宝登录：切到"淘宝登录"tab
                try:
                    tb_tab = page.ele("xpath://span[contains(text(),'淘宝登录')]", timeout=3)
                    if tb_tab:
                        logger.info("  切换到淘宝登录tab")
                        tb_tab.click()
                        time.sleep(3)  # 等待iframe重新加载
                except Exception as e:
                    logger.warning(f"  未找到淘宝登录tab: {e}")

            # 进入登录 iframe：淘宝登录(appName=taobao)用 login.jhtml 子账号框，
            # 普通登录(ascp)用 #alibaba-login-box。进错 iframe 会把账号密码填进隐藏表单，
            # 表现为“可见输入框没填进去”。
            if _app_name == "taobao":
                frame_locs = [
                    "xpath://iframe[contains(@src,'login.jhtml')]",
                    "xpath://iframe[contains(@src,'login.taobao.com/member')]",
                    "#alibaba-login-box",
                ]
            else:
                frame_locs = ["#alibaba-login-box"]

            ctx = page
            entered = False
            for floc in frame_locs:
                try:
                    fr = page.get_frame(floc)
                    if fr and fr.eles("tag:input"):
                        ctx = fr
                        entered = True
                        logger.info(f"  进入登录 iframe: {floc}")
                        time.sleep(1)  # 等待iframe内容稳定
                        break
                except Exception:
                    continue
            if not entered:
                logger.warning("  无法进入 login iframe，回退到直接页面操作")
        else:
            page.get(havana.HAVANA_LOGIN_URL)
            time.sleep(5)  # 淘宝会员登录页需要更多时间加载动态内容
            ctx = page

        # 填写账号
        logger.info("  填写账号密码...")
        login_input = None
        for sel in ["css:#fm-login-id", "css:input[name='loginId']",
                    "css:input[placeholder*='账号']", "css:input[placeholder*='手机']"]:
            try:
                login_input = ctx.ele(sel, timeout=3)
                if login_input:
                    logger.info(f"  找到账号框: {sel}")
                    break
            except Exception:
                pass
        if not login_input:
            page.get_screenshot(str(Path(__file__).parent / "debug_fallback.png"))
            logger.error("  未找到账号框")
            return None, "error:no_login_input"
        try:
            login_input.click()  # 先点击激活
            time.sleep(0.2)
            login_input.clear()
            time.sleep(0.2)
            login_input.input(havana.LOGIN_ID)
            time.sleep(0.5)
            # 读真实 property（attr('value') 对动态输入恒为 None，会谎报“空”）
            actual_value = _read_input_value(ctx, login_input)
            if not actual_value:
                # 兜底：JS 直接赋值并触发 input/change 事件
                _js_set_value(ctx, login_input, havana.LOGIN_ID)
                actual_value = _read_input_value(ctx, login_input)
            logger.info(f"  账号框值: {actual_value[:10] if actual_value else '(空)'}...")
            if not actual_value:
                page.get_screenshot(str(Path(__file__).parent / "debug_fallback.png"))
                logger.error("  账号填充失败（输入框仍为空），可能 iframe 选择错误")
                return None, "error:fill_login_empty"
        except Exception as e:
            logger.warning(f"  填写账号失败: {e}")
            return None, f"error:fill_login_failed:{e}"

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
            logger.error("  未找到密码框")
            return None, "error:no_password_input"
        pwd_input.clear()
        pwd_input.input(havana.PASSWORD)
        time.sleep(0.3)
        if not _read_input_value(ctx, pwd_input):
            _js_set_value(ctx, pwd_input, havana.PASSWORD)
        if not _read_input_value(ctx, pwd_input):
            page.get_screenshot(str(Path(__file__).parent / "debug_fallback.png"))
            logger.error("  密码填充失败（输入框仍为空）")
            return None, "error:fill_password_empty"

        # 点击登录
        logger.info("  点击登录...")
        login_btn = None
        # 优先查找文本是"登录"的按钮，避免匹配到弹窗按钮
        for sel in ["xpath://button[contains(text(),'登录') and not(contains(text(),'保持'))]",
                    "xpath://button[@type='submit' and contains(text(),'登录')]",
                    "css:#login-form button[type='submit']",
                    "css:.btn-login", "css:.login-btn"]:
            try:
                login_btn = ctx.ele(sel, timeout=2)
                if login_btn and login_btn.states.is_displayed:
                    # 检查按钮文本，排除弹窗按钮
                    btn_text = login_btn.text or ""
                    if "保持" not in btn_text or "登录" in btn_text:
                        break
                    else:
                        login_btn = None
            except Exception:
                pass
        if login_btn:
            try:
                login_btn.click()
            except Exception as e:
                logger.warning(f"  点击登录按钮失败: {type(e).__name__}, 尝试回车提交")
                pwd_input.input("\n")
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
                    logger.info("  已同意协议弹窗")
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

            if _browser_handle_sms(page, sms_wait=55):
                time.sleep(2)
            else:
                handle_nc_slider(page, max_retry=havana.SLIDER_RETRY)
                time.sleep(3)

        # 等待最终跳转
        for _ in range(15):
            if is_seller_logged_in_url(page.url):
                logger.info(f"  登录成功: {page.url}")
                break
            time.sleep(1)

        if is_seller_logged_in_url(page.url):
            browser_cookies = page.cookies()
            cookies_dict = {c["name"]: c["value"] for c in browser_cookies}
            page.quit()
            return cookies_dict, "success"

        status = "need_verify:iv" if is_verification_url(page.url) else "unknown"
        logger.warning(f"  登录未完成（status={status}），当前 URL: {page.url[:80]}")
        try:
            page.get_screenshot(str(Path(__file__).parent / "debug.png"))
        except Exception:
            pass
        page.quit()
        return None, status

    except Exception as exc:
        logger.error(f"  浏览器自动化异常: {exc}")
        if page:
            try:
                page.quit()
            except Exception:
                pass
        return None, f"error:{exc}"
