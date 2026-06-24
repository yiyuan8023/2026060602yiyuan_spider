"""
Havana 协议登录核心：配置管理、RSA加密、安全令牌提取、POST登录、重试降级、prepare_shop_cookie。
"""

from __future__ import annotations

import re
import json
import time
import base64
import hashlib
import logging
import sys
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlencode

import requests
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.backends import default_backend

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def load_local_taobao_login_config() -> dict:
    try:
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))
        from config.local_config import get_local_section

        local_config = get_local_section("taobao_login")
    except Exception:
        return {}

    defaults = local_config.get("defaults") or {}
    if not isinstance(defaults, dict):
        defaults = {}

    shops = local_config.get("shops") or []
    shop_config = {}
    if isinstance(shops, dict) and shops:
        shop_name, raw_config = next(iter(shops.items()))
        shop_config = raw_config.copy() if isinstance(raw_config, dict) else {}
        shop_config.setdefault("shop_name", shop_name)
    elif isinstance(shops, list) and shops:
        first_shop = shops[0]
        if isinstance(first_shop, dict):
            shop_config = first_shop.copy()
        elif isinstance(first_shop, str):
            shop_config = {"shop_name": first_shop}

    return {**defaults, **shop_config}


def load_config() -> dict:
    defaults = {
        "shop_name": "",
        "login_id": "",
        "password": "",
        "cookie_file": "taobao_cookies.json",
        "netscape_file": "taobao_cookies.txt",
        "timeout": 30,
        "max_retries": 3,
        "retry_delay": 5,
        "slider_retry": 4,
        "validate_url": "https://myseller.taobao.com/home.htm",
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/149.0.0.0 Safari/537.36"
        ),
    }
    defaults.update(load_local_taobao_login_config())
    return defaults


CFG = load_config()

PASSWORD = CFG["password"]
SHOP_NAME = CFG.get("shop_name") or ""
LOGIN_ID = CFG.get("login_id") or ""
COOKIE_FILE = Path(__file__).parent / CFG["cookie_file"]
NETSCAPE_FILE = Path(__file__).parent / CFG["netscape_file"]
TIMEOUT = CFG["timeout"]
MAX_RETRIES = CFG["max_retries"]
RETRY_DELAY = CFG["retry_delay"]
SLIDER_RETRY = int(CFG.get("slider_retry", 4))
VALIDATE_URL = CFG["validate_url"]
USER_AGENT = CFG["user_agent"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("tb_login")

BASE_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
}

HAVANA_LOGIN_URL = "https://login.taobao.com/havanaone/login/login.htm?bizName=taobao"
DEFAULT_COOKIE_SITE = "生意参谋"
DEFAULT_COOKIE_URL = "https://myseller.taobao.com/home.htm"
DEFAULT_COOKIE_DOMAIN = ".taobao.com"
DEFAULT_COOKIE_MAX_AGE_DAYS = 30


def configure_login(
    login_id: str | None = None,
    password: str | None = None,
    timeout: int | None = None,
    max_retries: int | None = None,
    retry_delay: int | None = None,
    slider_retry: int | None = None,
    validate_url: str | None = None,
    user_agent: str | None = None,
    havana_login_url: str | None = None,
) -> None:
    global PASSWORD, LOGIN_ID
    global TIMEOUT, MAX_RETRIES, RETRY_DELAY, SLIDER_RETRY, VALIDATE_URL, USER_AGENT, BASE_HEADERS
    global HAVANA_LOGIN_URL

    if login_id is not None:
        LOGIN_ID = login_id
    if password is not None:
        PASSWORD = password
    if timeout is not None:
        TIMEOUT = int(timeout)
    if max_retries is not None:
        MAX_RETRIES = int(max_retries)
    if retry_delay is not None:
        RETRY_DELAY = int(retry_delay)
    if slider_retry is not None:
        SLIDER_RETRY = int(slider_retry)
    if validate_url is not None:
        VALIDATE_URL = validate_url
    if user_agent is not None:
        USER_AGENT = user_agent
        BASE_HEADERS["User-Agent"] = USER_AGENT
    if havana_login_url is not None:
        HAVANA_LOGIN_URL = havana_login_url


def rsa_encrypt_password(n_hex: str, e_hex: str, plaintext: str) -> str:
    n = int(n_hex, 16)
    e = int(e_hex, 16)
    public_key = RSAPublicNumbers(e, n).public_key(default_backend())
    cipher = public_key.encrypt(plaintext.encode(), asym_padding.PKCS1v15())
    return base64.b64encode(cipher).decode()


def extract_json_var(html: str, var_name: str) -> dict | None:
    pattern = rf"(?:var|window\.)\s*{re.escape(var_name)}\s*=\s*(\{{.*?\}});"
    m = re.search(pattern, html, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    return None


def generate_page_trace_id() -> str:
    ts = str(int(time.time() * 1000))
    rand = uuid.uuid4().hex[:8]
    return f"{rand}{ts}0{rand[:4]}"


# ═══════════════════════════════════════════════
# 安全令牌
# ═══════════════════════════════════════════════

def extract_security_tokens() -> dict:
    log.info("  提取安全令牌 (AWSC SDK)...")
    try:
        from DrissionPage import ChromiumPage, ChromiumOptions
    except ImportError:
        log.warning("  DrissionPage 未安装，跳过令牌提取")
        return {}

    co = ChromiumOptions()
    co.auto_port(True)
    co.set_argument("--lang=zh-CN")
    co.set_argument("--disable-blink-features=AutomationControlled")
    co.set_pref("credentials_enable_service", False)
    co.set_pref("profile.password_manager_enabled", False)
    co.headless(True)

    tokens = {}
    page = None
    try:
        page = ChromiumPage(addr_or_opts=co)
        page.get(HAVANA_LOGIN_URL)
        time.sleep(4)

        init_result = page.run_js('''
            return new Promise(function(resolve) {
                var timeout = setTimeout(function() {
                    resolve({status: "timeout"});
                }, 15000);
                if (!window.AWSC || !window.AWSC.use) {
                    resolve({status: "no_awsc"});
                    return;
                }
                window.AWSC.use("um", function(state, module) {
                    if (state === "loaded" && module && module.init) {
                        module.init({appName: "taobao"}, function(initState, data) {
                            clearTimeout(timeout);
                            if (initState === "success" && data && data.tn) {
                                resolve({status: "success", data: data});
                            } else {
                                resolve({status: "init_failed", msg: initState});
                            }
                        });
                    } else {
                        clearTimeout(timeout);
                        resolve({status: "load_failed", msg: state});
                    }
                });
            });
        ''')

        if isinstance(init_result, str):
            init_result = json.loads(init_result)

        if init_result.get("status") == "success":
            umid_token = init_result["data"]["tn"]
            tokens["umidToken"] = umid_token
            log.info(f"  umidToken: {umid_token[:50]}...")
        else:
            log.warning(f"  umidToken 获取失败: {init_result}")

        ua_val = page.run_js('''
            if (window.baxiaCommon && typeof window.baxiaCommon.getUA === "function") {
                return window.baxiaCommon.getUA();
            }
            if (window.__baxia__ && window.__baxia__.getStore) {
                var fy = window.__baxia__.getStore("getFYModule", {});
                if (fy && typeof fy.getUA === "function") return fy.getUA();
            }
            return "";
        ''')
        if ua_val and "not_loaded" not in ua_val.lower():
            tokens["ua"] = ua_val
            log.info(f"  ua: {ua_val[:80]}...")
        else:
            log.warning(f"  ua 获取失败")

        browser_cookies = page.cookies()
        tokens["_cookies"] = {c["name"]: c["value"] for c in browser_cookies}
        log.info(f"  浏览器 cookies: {list(tokens['_cookies'].keys())[:10]}")

        page.quit()
        page = None
    except Exception as exc:
        log.warning(f"  安全令牌提取失败: {exc}")
        import traceback
        traceback.print_exc()
    finally:
        if page:
            try:
                page.quit()
            except Exception:
                pass

    return tokens


def get_security_tokens() -> dict:
    try:
        try:
            from ..protocol_login.iv8_token_provider import get_security_tokens_iv8
        except ImportError:
            from protocol_login.iv8_token_provider import get_security_tokens_iv8

        tokens = get_security_tokens_iv8(user_agent=USER_AGENT, timeout=TIMEOUT)
        if tokens.get("umidToken") and tokens.get("ua"):
            log.info("  采用 iv8 纯协议安全令牌（无浏览器）")
            return tokens
        log.info("  iv8 令牌不可用，回落 DrissionPage 提取")
    except Exception as exc:
        log.warning(f"  iv8 令牌提取异常，回落 DrissionPage: {type(exc).__name__}: {exc}")
    return extract_security_tokens()


def _try_solve_iv_sms(session: "requests.Session", redirect_url: str) -> bool:
    try:
        try:
            from ..protocol_login.iv_sms_solver import solve_iv_sms
        except ImportError:
            from protocol_login.iv_sms_solver import solve_iv_sms
        return solve_iv_sms(session, redirect_url, sms_wait=120, timeout=TIMEOUT)
    except Exception as exc:
        log.warning(f"  IV 短信求解调用失败: {type(exc).__name__}: {exc}")
        return False


# ═══════════════════════════════════════════════
# 协议登录
# ═══════════════════════════════════════════════

def login(security_tokens: dict = None, st_callback=None) -> tuple[dict | None, str]:
    """
    Havana 协议登录。st_callback(session, st, st2, return_url) 用于自定义ST回调。
    默认 None 时走简单 returnUrl?st=xxx。
    """
    if security_tokens is None:
        security_tokens = {}

    session = requests.Session()
    session.headers.update(BASE_HEADERS)

    browser_cookies = security_tokens.get("_cookies", {})
    if browser_cookies:
        for name, val in browser_cookies.items():
            session.cookies.set(name, val, domain=".taobao.com")

    log.info("=" * 55)
    log.info("Step 1 > 访问 Havana 登录页...")
    try:
        r1 = session.get(HAVANA_LOGIN_URL, timeout=TIMEOUT)
    except Exception as exc:
        log.error(f"  网络请求失败: {exc}")
        return None, f"network_error:{exc}"

    log.info(f"  状态码: {r1.status_code}")
    log.info(f"  Cookies: {[c.name for c in session.cookies]}")

    log.info("Step 2 > 提取页面配置...")
    view_config = extract_json_var(r1.text, "viewConfig")
    view_data = extract_json_var(r1.text, "viewData")

    if not view_config or not view_data:
        log.error("  无法提取 viewConfig/viewData")
        return None, "error:page_parse_failed"

    rsa_modulus = view_config.get("rsaModulus", "")
    rsa_exponent = view_config.get("rsaExponent", "10001")
    log.info(f"  RSA modulus (前40): {rsa_modulus[:40]}...")

    api_config = view_config.get("api", {})
    login_api = api_config.get("loginApi", "")
    if not login_api:
        log.error("  未找到 loginApi")
        return None, "error:no_login_api"
    log.info(f"  Login API: {login_api}")

    login_form_data = view_data.get("loginFormData", {})
    log.info(f"  loginFormData: {list(login_form_data.keys())}")

    if not rsa_modulus:
        log.error("  RSA modulus 为空")
        return None, "error:no_rsa_key"

    log.info("Step 3 > RSA 加密密码...")
    try:
        encrypted_pwd = rsa_encrypt_password(rsa_modulus, rsa_exponent, PASSWORD)
        log.info(f"  加密成功 (前40): {encrypted_pwd[:40]}...")
    except Exception as exc:
        log.error(f"  RSA 加密失败: {exc}")
        return None, f"error:rsa_encrypt_failed:{exc}"

    log.info("Step 4 > POST 登录请求...")
    post_data = {}
    post_data.update(login_form_data)
    post_data.update({
        "loginId": LOGIN_ID,
        "password2": encrypted_pwd,
        "keepLogin": "false",
        "ua": security_tokens.get("ua", ""),
        "umidGetStatusVal": security_tokens.get("umidGetStatusVal", "255"),
        "umidToken": security_tokens.get("umidToken", ""),
        "umidTag": "WEB" if security_tokens.get("umidToken") else "NOT_INIT",
        "navlanguage": "zh-CN",
        "navUserAgent": USER_AGENT,
        "navPlatform": "Win32",
        "isIframe": "false",
        "banThirdPartyCookie": "false",
        "documentReferer": "",
        "defaultView": "password",
        "pageTraceId": generate_page_trace_id(),
    })
    if security_tokens.get("deviceId"):
        post_data["deviceId"] = security_tokens["deviceId"]

    login_url = f"https://login.taobao.com{login_api}"
    log.info(f"  POST URL: {login_url}")
    log.info(f"  umidToken: {'(有)' if post_data.get('umidToken') else '(空)'}")
    log.info(f"  ua: {'(有)' if post_data.get('ua') else '(空)'}")

    session.headers.update({
        "Referer": HAVANA_LOGIN_URL,
        "Origin": "https://login.taobao.com",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    })

    try:
        r2 = session.post(login_url, data=post_data, timeout=TIMEOUT)
    except Exception as exc:
        log.error(f"  POST 失败: {exc}")
        return None, f"network_error:{exc}"

    log.info(f"  响应状态码: {r2.status_code}")

    log.info("Step 5 > 解析登录结果...")
    try:
        resp_json = r2.json()
        log.info(f"  JSON: {json.dumps(resp_json, ensure_ascii=False)[:500]}")

        ret_list = resp_json.get("ret", [])
        data = resp_json.get("data", {})
        if not data:
            content = resp_json.get("content", {})
            data = content.get("data", {})

        ret_str = " ".join(ret_list) if ret_list else ""

        if "RGV587_ERROR" in ret_str:
            log.warning(f"  触发风控: {ret_str}")
            return {c.name: c.value for c in session.cookies}, "captcha"

        if "FAIL_SYS_USER_VALIDATE" in ret_str and "RGV587" not in ret_str:
            log.warning(f"  账号/密码错误: {ret_str}")
            return {c.name: c.value for c in session.cookies}, f"error:{ret_str}"

        if data.get("isCheckCodeShowed"):
            log.warning("  触发验证码")
            return {c.name: c.value for c in session.cookies}, "captcha"

        title_msg = data.get("titleMsg", "")
        if title_msg:
            log.warning(f"  错误提示: {title_msg}")
            return {c.name: c.value for c in session.cookies}, f"error:{title_msg}"

        redirect_url = (
            data.get("redirectUrl", "")
            or data.get("parentRedirect", "")
            or data.get("url", "")
        )
        if not redirect_url and isinstance(data.get("redirect"), str):
            redirect_url = data["redirect"]
        async_urls = data.get("asyncUrls", [])
        login_result = data.get("loginResult", "")

        # IV 二次验证拦截
        from .cookie_manager import validate_cookies
        if (redirect_url and isinstance(redirect_url, str)
                and login_result != "success"
                and ("/iv/" in redirect_url or "havana_iv_token" in redirect_url)):
            log.warning(f"  触发 IV 二次身份验证: {redirect_url[:50]}...")
            if _try_solve_iv_sms(session, redirect_url):
                try:
                    session.get(VALIDATE_URL, timeout=TIMEOUT)
                except Exception:
                    pass
                for url in async_urls[:5]:
                    try:
                        session.get(url, timeout=10)
                    except Exception:
                        pass
                cookies = {c.name: c.value for c in session.cookies}
                if validate_cookies(cookies):
                    log.info("  IV 短信验证通过，登录态有效")
                    return cookies, "success"
                log.warning("  IV 已提交但登录态校验未通过")
            return {c.name: c.value for c in session.cookies}, "need_verify:iv"

        is_success = (
            login_result == "success"
            or "SUCCESS" in ret_str
            or (data.get("st") and data.get("asyncUrls"))
            or (redirect_url and isinstance(redirect_url, str)
                and "login" not in redirect_url.lower()
                and "punish" not in redirect_url.lower()
                and "/iv/" not in redirect_url.lower())
        )

        if is_success:
            log.info(f"  登录成功! 重定向: {redirect_url}")
            if redirect_url:
                try:
                    r3 = session.get(redirect_url, timeout=TIMEOUT)
                    log.info(f"  重定向后 URL: {r3.url}")
                except Exception as exc:
                    log.warning(f"  跟随重定向失败: {exc}")

            for url in async_urls[:5]:
                try:
                    session.get(url, timeout=10)
                except Exception:
                    pass

            # ST 回调
            st_token = data.get("st", "")
            st2_token = data.get("st2", "")
            return_url = login_form_data.get("returnUrl", "")
            if st_token and return_url:
                if st_callback:
                    st_callback(session, st_token, st2_token, return_url)
                else:
                    st_cb_url = f"{return_url}{'&' if '?' in return_url else '?'}st={st_token}"
                    log.info(f"  ST 回调: {st_cb_url[:80]}...")
                    try:
                        session.get(st_cb_url, timeout=TIMEOUT)
                    except Exception as exc:
                        log.warning(f"  ST 回调失败: {exc}")

            return {c.name: c.value for c in session.cookies}, "success"

        change_view = data.get("changeView", "")
        if change_view:
            log.warning(f"  需要切换验证方式: {change_view}")
            return {c.name: c.value for c in session.cookies}, f"need_verify:{change_view}"

        log.warning("  未识别的响应结构")
        return {c.name: c.value for c in session.cookies}, "unknown"

    except ValueError:
        log.warning(f"  响应非 JSON: {r2.text[:300]}")
        if r2.status_code in (301, 302, 303):
            loc = r2.headers.get("Location", "")
            if loc and "login" not in loc.lower():
                log.info(f"  302 重定向 (可能成功): {loc}")
                try:
                    session.get(loc, timeout=TIMEOUT)
                except Exception:
                    pass
                return {c.name: c.value for c in session.cookies}, "success"
        return {c.name: c.value for c in session.cookies}, "unknown"


# ═══════════════════════════════════════════════
# 重试与降级
# ═══════════════════════════════════════════════

def login_with_retry(st_callback=None) -> tuple[dict | None, str]:
    from .browser_fallback import browser_login_fallback

    log.info("Step 0 > 提取 AWSC 安全令牌...")
    security_tokens = get_security_tokens()
    has_tokens = bool(security_tokens.get("umidToken") and security_tokens.get("ua"))

    if has_tokens:
        log.info(f"  令牌提取成功，尝试协议登录")
    else:
        log.warning(f"  令牌提取不完整，协议登录可能被拦截")

    log.info("登录尝试: 协议模式")
    cookies, status = login(security_tokens=security_tokens, st_callback=st_callback)

    if status == "success":
        return cookies, status

    log.info("")
    log.info("协议登录被风控拦截，降级到浏览器自动化方案...")
    log.info("")
    cookies, status = browser_login_fallback()
    return cookies, status


# ═══════════════════════════════════════════════
# 高层调度
# ═══════════════════════════════════════════════

def prepare_shop_cookie(
    shop_name: str,
    login_id: str | None = None,
    password: str | None = None,
    db_cookie_str: str | None = None,
    db_cookie: str | dict | list | None = None,
    site: str = DEFAULT_COOKIE_SITE,
    save_local: bool = False,
    st_callback=None,
    **login_options,
) -> dict[str, Any]:
    configure_login(
        login_id=login_id,
        password=password,
        timeout=login_options.get("timeout"),
        max_retries=login_options.get("max_retries"),
        retry_delay=login_options.get("retry_delay"),
        slider_retry=login_options.get("slider_retry"),
        validate_url=login_options.get("validate_url"),
        user_agent=login_options.get("user_agent"),
        havana_login_url=login_options.get("havana_login_url"),
    )

    from .cookie_manager import (
        load_cookies_database, merge_cookie_sources,
        validate_and_refresh_cookies, validate_cookies,
        save_cookies_database, save_cookies_json, save_cookies_netscape,
    )

    log.info(f"{shop_name} 开始准备淘宝登录 Cookie，站点={site}")
    if not db_cookie_str and not db_cookie:
        db_cookie_str, db_cookie = load_cookies_database(site, shop_name)

    existing_cookies = merge_cookie_sources(db_cookie_str, db_cookie)
    if existing_cookies:
        log.info(f"{shop_name} 发现数据库 Cookie，先验证有效性")
        cookie_valid, refreshed_cookies = validate_and_refresh_cookies(existing_cookies)
        if cookie_valid:
            log.info(f"{shop_name} 数据库 Cookie 有效，刷新后回写 get_cookie")
            saved_to_db = False
            try:
                save_cookies_database(
                    shop_name=shop_name,
                    cookies=refreshed_cookies,
                    site=site,
                    login_id=LOGIN_ID or None,
                    yingdao_account=login_options.get("yingdao_account"),
                    maintainer_email=login_options.get("maintainer_email"),
                )
                saved_to_db = True
            except Exception as exc:
                log.warning(f"{shop_name} 刷新 Cookie 回写失败：{type(exc).__name__}: {exc}")
            return {
                "shop_name": shop_name,
                "site": site,
                "status": "db_cookie_valid",
                "cookie_count": len(refreshed_cookies),
                "saved_to_db": saved_to_db,
            }
        log.info(f"{shop_name} 数据库 Cookie 已失效，开始重新登录")
    else:
        log.info(f"{shop_name} 未获取到数据库 Cookie，开始重新登录")

    if not LOGIN_ID or not PASSWORD:
        raise RuntimeError(f"{shop_name} 缺少账号或密码，无法重新登录")

    cookies, status = login_with_retry(st_callback=st_callback)
    log.info("=" * 55)
    log.info(f"{shop_name} 登录结果: {status}")

    if status == "success" and cookies:
        if not validate_cookies(cookies):
            log.warning(f"{shop_name} 新登录 Cookie 校验未通过，跳过写库")
            return {
                "shop_name": shop_name,
                "site": site,
                "status": "error:new_cookie_invalid",
                "cookie_count": len(cookies),
                "saved_to_db": False,
            }

        log.info(f"{shop_name} 新登录 Cookie 校验通过，写入 get_cookie")
        cookie_header = save_cookies_database(
            shop_name=shop_name,
            cookies=cookies,
            site=site,
            login_id=LOGIN_ID,
            yingdao_account=login_options.get("yingdao_account"),
            maintainer_email=login_options.get("maintainer_email"),
        )
        if save_local:
            save_cookies_json(cookies, COOKIE_FILE)
            save_cookies_netscape(cookies, "taobao.com", NETSCAPE_FILE)
        return {
            "shop_name": shop_name,
            "site": site,
            "status": status,
            "cookie_count": len(cookies),
            "cookie_str_len": len(cookie_header),
            "saved_to_db": True,
        }

    return {
        "shop_name": shop_name,
        "site": site,
        "status": status,
        "cookie_count": len(cookies or {}),
        "saved_to_db": False,
    }
