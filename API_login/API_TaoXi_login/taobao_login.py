#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
淘宝卖家后台 (生意参谋) 协议级登录 & Cookie 管理脚本

目标站点 : https://login.taobao.com/havanaone/login/login.htm
最终输出 : taobao_cookies.json  (可直接用于后续请求)
"""

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

# ═══════════════════════════════════════════════
# 配置加载
# ═══════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_local_taobao_login_config() -> dict:
    """读取项目级 config/local.json 中第一条淘宝登录配置，供直接运行脚本兼容。"""
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

# 验证/惩罚页特征：这些 URL 不是登录成功态，Cookie 不可用
VERIFICATION_URL_MARKERS = (
    "/iv/", "normal_validate", "login_check", "havana_iv_token",
    "punish", "_____tmd_____", "nocaptcha", "captcha",
)


def is_verification_url(url: str) -> bool:
    """判断是否停留在风控验证/惩罚页（IV 二次验证、滑块、短信验证等）。"""
    lowered = (url or "").lower()
    return any(marker in lowered for marker in VERIFICATION_URL_MARKERS)


def is_seller_logged_in_url(url: str) -> bool:
    """判断浏览器是否真正进入已登录态（卖家后台等），排除登录页与验证页。"""
    lowered = (url or "").lower()
    if not lowered or "login" in lowered or is_verification_url(lowered):
        return False
    return "taobao.com" in lowered or "tmall.com" in lowered or "alibaba.com" in lowered


# ═══════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════

def rsa_encrypt_password(n_hex: str, e_hex: str, plaintext: str) -> str:
    """RSA PKCS1_v1_5 加密密码，返回十六进制字符串（Havana 格式）。"""
    e_int = int(e_hex, 16)
    n_int = int(n_hex, 16)
    pub_key = RSAPublicNumbers(e_int, n_int).public_key(default_backend())
    ciphertext = pub_key.encrypt(plaintext.encode("utf-8"), asym_padding.PKCS1v15())
    return ciphertext.hex()


def extract_json_var(html: str, var_name: str) -> dict | None:
    """从 HTML 中提取 window.xxx = {...} 形式的 JSON 对象。"""
    pattern = rf"window\.{var_name}\s*=\s*(\{{.*?\}});\s*\n"
    m = re.search(pattern, html, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    return None


def generate_page_trace_id() -> str:
    """生成 pageTraceId，格式类似淘宝的 traceId。"""
    ts = str(int(time.time() * 1000))
    rand = uuid.uuid4().hex[:8]
    return f"{rand}{ts}0{rand[:4]}"


def configure_login(
    login_id: str | None = None,
    password: str | None = None,
    timeout: int | None = None,
    max_retries: int | None = None,
    retry_delay: int | None = None,
    slider_retry: int | None = None,
    validate_url: str | None = None,
    user_agent: str | None = None,
) -> None:
    """用 jobs_login 传入的店铺配置覆盖模块级登录参数。"""
    global PASSWORD, LOGIN_ID
    global TIMEOUT, MAX_RETRIES, RETRY_DELAY, SLIDER_RETRY, VALIDATE_URL, USER_AGENT, BASE_HEADERS

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


# ═══════════════════════════════════════════════
# Cookie 管理
# ═══════════════════════════════════════════════

def save_cookies_json(cookies: dict, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)
    log.info(f"JSON cookies 已保存 -> {path}")


def save_cookies_netscape(cookies: dict, domain: str, path: Path) -> None:
    lines = ["# Netscape HTTP Cookie File\n"]
    ts = int(time.time()) + 86400 * 30
    for name, value in cookies.items():
        lines.append(f".{domain}\tTRUE\t/\tFALSE\t{ts}\t{name}\t{value}\n")
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    log.info(f"Netscape cookies 已保存 -> {path}")


def load_cookies_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and len(data) > 0:
            return data
    except (json.JSONDecodeError, IOError):
        pass
    return None


def cookie_header_to_dict(cookie_header: str | None) -> dict[str, str]:
    """把数据库 cookie_str 转为 requests 可用的 dict。"""
    if not cookie_header:
        return {}

    cookies = {}
    for item in str(cookie_header).split(";"):
        if "=" not in item:
            continue
        name, value = item.strip().split("=", 1)
        if name:
            cookies[name] = value
    return cookies


def browser_cookie_json_to_dict(cookie_json: str | dict | list | None) -> dict[str, str]:
    """兼容 cookie 表中浏览器 JSON 和本地 dict 两种 Cookie 存储形态。"""
    if not cookie_json:
        return {}

    if isinstance(cookie_json, str):
        try:
            payload: Any = json.loads(cookie_json)
        except json.JSONDecodeError:
            return {}
    else:
        payload = cookie_json

    if isinstance(payload, list):
        cookie_items = payload
    elif isinstance(payload, dict) and isinstance(payload.get("cookies"), list):
        cookie_items = payload["cookies"]
    elif isinstance(payload, dict):
        return {str(name): str(value) for name, value in payload.items() if value is not None}
    else:
        return {}

    cookies = {}
    for item in cookie_items:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        value = item.get("value")
        if name and value is not None:
            cookies[str(name)] = str(value)
    return cookies


def merge_cookie_sources(cookie_str: str | None = None, cookie_json: str | dict | list | None = None) -> dict[str, str]:
    """优先使用 cookie_str，并补充 cookie JSON 中缺失的键。"""
    cookies = browser_cookie_json_to_dict(cookie_json)
    cookies.update(cookie_header_to_dict(cookie_str))
    return cookies


def cookie_dict_to_header(cookies: dict[str, str]) -> str:
    """把 dict 转成标准 HTTP Cookie header。"""
    return "; ".join(f"{name}={value}" for name, value in cookies.items() if value is not None)


def cookie_dict_to_browser_items(
    cookies: dict[str, str],
    domain: str = DEFAULT_COOKIE_DOMAIN,
    max_age_days: int = DEFAULT_COOKIE_MAX_AGE_DAYS,
) -> list[dict[str, Any]]:
    """把协议登录返回的 dict 转成 get_cookie.cookie 使用的浏览器 Cookie 列表。"""
    expires = int(time.time()) + 86400 * max_age_days
    return [
        {
            "name": str(name),
            "value": str(value),
            "domain": domain,
            "path": "/",
            "expires": expires,
            "httpOnly": False,
            "secure": False,
            "sameSite": "Lax",
        }
        for name, value in cookies.items()
        if value is not None
    ]


def save_cookies_database(
    shop_name: str,
    cookies: dict[str, str],
    site: str = DEFAULT_COOKIE_SITE,
    login_id: str | None = None,
    yingdao_account: str | None = None,
    maintainer_email: str | None = None,
) -> str:
    """把登录成功 Cookie 写入 get_cookie，读取仍走 cookie 视图。"""
    from database import DBManager

    cookie_header = cookie_dict_to_header(cookies)
    cookie_payload = json.dumps(
        {
            "url": DEFAULT_COOKIE_URL,
            "cookies": cookie_dict_to_browser_items(cookies),
        },
        ensure_ascii=False,
    )
    cookie_dict_text = json.dumps(cookies, ensure_ascii=False)
    with DBManager() as db_manager:
        db_manager.upsert_cookie(
            site=site,
            shop_name=shop_name,
            cookie_str=cookie_header,
            cookie=cookie_payload,
            cookie_dict=cookie_dict_text,
            account=login_id,
            yingdao_account=yingdao_account,
            maintainer_email=maintainer_email,
        )
    log.info(f"{shop_name} Cookie 已写入 get_cookie，站点={site}")
    return cookie_header


def load_cookies_database(site: str, shop_name: str) -> tuple[str | None, str | None]:
    """从 cookie 视图读取已保存 Cookie；写入仍只写 get_cookie。"""
    from database import DBManager

    with DBManager() as db_manager:
        row = db_manager.select_cookie(site, shop_name)
    if not row:
        return None, None
    return row[1], row[2]


def validate_cookies(cookies: dict) -> bool:
    """验证已保存的 cookies 是否仍然有效。"""
    required_keys = {"unb", "cookie2"}
    if not required_keys & set(cookies.keys()):
        log.info("  Cookie 缺少关键字段，需重新登录")
        return False

    log.info("  验证 Cookie 有效性...")
    try:
        session = requests.Session()
        session.headers.update(BASE_HEADERS)
        session.cookies.update(cookies)
        resp = session.get(VALIDATE_URL, timeout=TIMEOUT, allow_redirects=False)
        if resp.status_code == 200:
            log.info("  Cookie 有效")
            return True
        if resp.status_code in (301, 302):
            location = resp.headers.get("Location", "")
            if "login" in location.lower():
                log.info("  Cookie 已过期")
                return False
            log.info("  Cookie 有效 (非登录重定向)")
            return True
    except Exception as exc:
        log.warning(f"  验证请求失败: {exc}")
    return False


def validate_and_refresh_cookies(cookies: dict) -> tuple[bool, dict]:
    """
    用已有 Cookie 访问卖家后台：既校验有效性，又捕获服务端 Set-Cookie 的滚动刷新。

    返回 (是否有效, 刷新后的 Cookie)。有效时返回原 Cookie 合并本次会话刷新值（滑动续期、
    轮转令牌如 isg/tfstk/_m_h5_tk 更新）；无效或异常时返回 (False, 原 Cookie)。
    不做密码登录、不触发风控、不发短信。
    """
    required_keys = {"unb", "cookie2"}
    if not required_keys & set(cookies.keys()):
        log.info("  Cookie 缺少关键字段，需重新登录")
        return False, cookies

    log.info("  用有效 Cookie 访问后台并刷新...")
    try:
        session = requests.Session()
        session.headers.update(BASE_HEADERS)
        session.cookies.update(cookies)
        resp = session.get(VALIDATE_URL, timeout=TIMEOUT, allow_redirects=True)
        if resp.status_code == 200 and "login" not in resp.url.lower():
            # 原 Cookie 打底，叠加本次会话(含 Set-Cookie)刷新值
            refreshed = dict(cookies)
            refreshed.update(session.cookies.get_dict())
            log.info(f"  Cookie 有效，已刷新（{len(refreshed)} 项）")
            return True, refreshed
        log.info("  Cookie 已过期")
    except Exception as exc:
        log.warning(f"  校验/刷新请求失败: {exc}")
    return False, cookies


# ═══════════════════════════════════════════════
# Havana 协议登录
# ═══════════════════════════════════════════════

def extract_security_tokens() -> dict:
    """
    使用 DrissionPage 打开登录页，触发 AWSC 安全 SDK 初始化，
    提取 umidToken (设备指纹) 和 ua (行为指纹)。
    """
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

        # 手动触发 AWSC.configFY 初始化 um 模块
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

        # 提取 UA (bx-ua 行为指纹)
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

        # 提取浏览器 cookies (含安全 SDK 写入的)
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
    """优先用 iv8 纯协议提取 AWSC 令牌（umidToken + bx-ua），失败回落 DrissionPage 浏览器提取。"""
    try:
        try:
            from .protocol_login.iv8_token_provider import get_security_tokens_iv8
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
    """命中 IV 二次验证时，尝试纯协议短信求解；任何异常都不抛出，交由上层兜底。"""
    try:
        try:
            from .protocol_login.iv_sms_solver import solve_iv_sms
        except ImportError:
            from protocol_login.iv_sms_solver import solve_iv_sms
        return solve_iv_sms(session, redirect_url, sms_wait=120, timeout=TIMEOUT)
    except Exception as exc:
        log.warning(f"  IV 短信求解调用失败: {type(exc).__name__}: {exc}")
        return False


def login(security_tokens: dict = None) -> tuple[dict | None, str]:
    """
    Havana 协议登录流程:
    1. 访问登录页获取 cookies + 内嵌配置 (RSA密钥, CSRF, API路径)
    2. RSA 加密密码
    3. POST 到 password/login.do (附带安全令牌)
    4. 跟随重定向至卖家后台
    """
    if security_tokens is None:
        security_tokens = {}

    session = requests.Session()
    session.headers.update(BASE_HEADERS)

    # 如果有浏览器 cookies，先注入（包含安全 SDK 的 cookie）
    browser_cookies = security_tokens.get("_cookies", {})
    if browser_cookies:
        for name, val in browser_cookies.items():
            session.cookies.set(name, val, domain=".taobao.com")

    # ── Step 1: 访问 Havana 登录页 ──
    log.info("=" * 55)
    log.info("Step 1 > 访问 Havana 登录页...")
    try:
        r1 = session.get(HAVANA_LOGIN_URL, timeout=TIMEOUT)
    except Exception as exc:
        log.error(f"  网络请求失败: {exc}")
        return None, f"network_error:{exc}"

    log.info(f"  状态码: {r1.status_code}")
    log.info(f"  Cookies: {[c.name for c in session.cookies]}")

    # ── Step 2: 提取页面配置 ──
    log.info("Step 2 > 提取页面配置...")
    view_config = extract_json_var(r1.text, "viewConfig")
    view_data = extract_json_var(r1.text, "viewData")

    if not view_config or not view_data:
        log.error("  无法提取 viewConfig/viewData")
        return None, "error:page_parse_failed"

    # RSA 密钥
    rsa_modulus = view_config.get("rsaModulus", "")
    rsa_exponent = view_config.get("rsaExponent", "10001")
    log.info(f"  RSA modulus (前40): {rsa_modulus[:40]}...")
    log.info(f"  RSA exponent: {rsa_exponent}")

    # API 路径
    api_config = view_config.get("api", {})
    login_api = api_config.get("loginApi", "")
    if not login_api:
        log.error("  未找到 loginApi")
        return None, "error:no_login_api"
    log.info(f"  Login API: {login_api}")

    # loginFormData (基础参数)
    login_form_data = view_data.get("loginFormData", {})
    csrf_token = login_form_data.get("_csrf", "")
    log.info(f"  _csrf: {csrf_token}")
    log.info(f"  loginFormData: {list(login_form_data.keys())}")

    if not rsa_modulus:
        log.error("  RSA modulus 为空")
        return None, "error:no_rsa_key"

    # ── Step 3: 加密密码 ──
    log.info("Step 3 > RSA 加密密码...")
    try:
        encrypted_pwd = rsa_encrypt_password(rsa_modulus, rsa_exponent, PASSWORD)
        log.info(f"  加密成功 (前40): {encrypted_pwd[:40]}...")
    except Exception as exc:
        log.error(f"  RSA 加密失败: {exc}")
        return None, f"error:rsa_encrypt_failed:{exc}"

    # ── Step 4: 构造并发送登录请求 ──
    log.info("Step 4 > POST 登录请求...")

    post_data = {}
    # 基础参数 (来自 loginFormData)
    post_data.update(login_form_data)
    # 登录参数
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
    log.info(f"  响应长度: {len(r2.content)} bytes")

    # ── Step 5: 解析登录结果 ──
    log.info("Step 5 > 解析登录结果...")
    try:
        resp_json = r2.json()
        log.info(f"  JSON: {json.dumps(resp_json, ensure_ascii=False)[:500]}")

        # Havana 响应格式: {ret: [...], data: {...}} 或 {content: {data: {...}}}
        ret_list = resp_json.get("ret", [])
        data = resp_json.get("data", {})
        if not data:
            content = resp_json.get("content", {})
            data = content.get("data", {})

        # 检查 ret 字段中的状态
        ret_str = " ".join(ret_list) if ret_list else ""

        # 风控拦截 (RGV587_ERROR)
        if "RGV587_ERROR" in ret_str:
            log.warning(f"  触发风控: {ret_str}")
            return {c.name: c.value for c in session.cookies}, "captcha"

        # 密码错误
        if "FAIL_SYS_USER_VALIDATE" in ret_str and "RGV587" not in ret_str:
            log.warning(f"  账号/密码错误: {ret_str}")
            return {c.name: c.value for c in session.cookies}, f"error:{ret_str}"

        # 检查是否需要验证码
        if data.get("isCheckCodeShowed"):
            log.warning("  触发验证码")
            return {c.name: c.value for c in session.cookies}, "captcha"

        # 检查错误信息
        title_msg = data.get("titleMsg", "")
        if title_msg:
            log.warning(f"  错误提示: {title_msg}")
            return {c.name: c.value for c in session.cookies}, f"error:{title_msg}"

        # 检查重定向 URL (登录成功标志)
        redirect_url = (
            data.get("redirectUrl", "")
            or data.get("parentRedirect", "")
            or data.get("url", "")
        )
        # data.redirect 可能是布尔值 true，不是 URL
        if not redirect_url and isinstance(data.get("redirect"), str):
            redirect_url = data["redirect"]
        async_urls = data.get("asyncUrls", [])
        login_result = data.get("loginResult", "")

        # IV 二次身份验证：loginResult 非 success 且跳转到 /iv/ 验证页（baxia NC 滑块）。
        # 必须在 is_success 之前拦截，否则会被误判为成功并写入无效 Cookie。
        if (redirect_url and isinstance(redirect_url, str)
                and login_result != "success"
                and ("/iv/" in redirect_url or "havana_iv_token" in redirect_url)):
            log.warning(f"  触发 IV 二次身份验证，尝试纯协议短信求解: {redirect_url[:50]}...")
            if _try_solve_iv_sms(session, redirect_url):
                # IV 通过：补全跨域 Cookie（卖家后台 + asyncUrls）后校验登录态
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

        # 成功标志: loginResult == "success" 或 ret 包含 SUCCESS
        is_success = (
            login_result == "success"
            or "SUCCESS" in ret_str
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

            return {c.name: c.value for c in session.cookies}, "success"

        # 检查 changeView (需要切换验证方式)
        change_view = data.get("changeView", "")
        if change_view:
            log.warning(f"  需要切换验证方式: {change_view}")
            return {c.name: c.value for c in session.cookies}, f"need_verify:{change_view}"

        log.warning("  未识别的响应结构")
        return {c.name: c.value for c in session.cookies}, "unknown"

    except ValueError:
        # 非 JSON 响应
        log.warning(f"  响应非 JSON: {r2.text[:300]}")

        # 检查是否是 302 重定向
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


def login_with_retry() -> tuple[dict | None, str]:
    """带重试和降级的登录。协议登录失败时自动降级到浏览器自动化。"""
    # Step 0: 提取安全令牌（iv8 纯协议优先，DrissionPage 兜底）
    log.info("Step 0 > 提取 AWSC 安全令牌...")
    security_tokens = get_security_tokens()
    has_tokens = bool(security_tokens.get("umidToken") and security_tokens.get("ua"))

    if has_tokens:
        log.info(f"  令牌提取成功，尝试协议登录")
    else:
        log.warning(f"  令牌提取不完整，协议登录可能被拦截")

    # 第一次尝试：协议登录（带安全令牌）
    log.info("登录尝试: 协议模式")
    cookies, status = login(security_tokens=security_tokens)

    if status == "success":
        return cookies, status

    # 协议登录被风控拦截，降级到浏览器自动化
    log.info("")
    log.info("协议登录被风控拦截，降级到浏览器自动化方案...")
    log.info("")
    cookies, status = browser_login_fallback()
    return cookies, status


def _browser_handle_sms(page: Any, sms_wait: int = 90) -> bool:
    """
    浏览器端短信验证处理，兼容 IV identity_verify 页（#J_GetCode/#J_Phone_Checkcode）
    与普通登录短信页（占位符选择器）。点发码 → 邮箱读码 → 填入 → 提交，成功返回 True。
    """
    try:
        try:
            from .sms_helper import get_sms_code
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
    """使用浏览器自动化完成登录（含 NC 滑块与 IV 短信验证自动处理）。"""
    try:
        from DrissionPage import ChromiumPage, ChromiumOptions
    except ImportError:
        log.error("DrissionPage 未安装，无法使用浏览器降级方案")
        return None, "error:no_drissionpage"

    # 短信处理在 _browser_handle_sms 内自行导入 get_sms_code，这里只需滑块能力
    try:
        from .auto_login.slider_helper import handle_nc_slider
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
        page.get(HAVANA_LOGIN_URL)
        time.sleep(3)

        # 切到密码登录 tab
        try:
            pwd_tab = page.ele("xpath://span[contains(text(),'密码登录')]", timeout=3)
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
                login_input = page.ele(sel, timeout=3)
                if login_input:
                    break
            except Exception:
                pass
        if not login_input:
            page.get_screenshot(str(Path(__file__).parent / "debug_fallback.png"))
            log.error("  未找到账号框")
            return None, "error:no_login_input"
        login_input.clear()
        login_input.input(LOGIN_ID)
        time.sleep(0.3)

        # 填写密码
        pwd_input = None
        for sel in ["css:#fm-login-password", "css:input[type='password']",
                    "css:input[name='password']", "css:input[placeholder*='密码']"]:
            try:
                pwd_input = page.ele(sel, timeout=3)
                if pwd_input:
                    break
            except Exception:
                pass
        if not pwd_input:
            page.get_screenshot(str(Path(__file__).parent / "debug_fallback.png"))
            log.error("  未找到密码框")
            return None, "error:no_password_input"
        pwd_input.clear()
        pwd_input.input(PASSWORD)
        time.sleep(0.3)

        # 点击登录
        log.info("  点击登录...")
        login_btn = None
        for sel in ["css:#login-form button[type='submit']", "css:button[type='submit']",
                    "css:.btn-login", "css:.login-btn"]:
            try:
                login_btn = page.ele(sel, timeout=3)
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
        agree_sels = [
            "xpath://button[text()='同意']",
            "xpath://div[text()='同意']",
            "xpath://span[text()='同意']",
        ]
        for sel in agree_sels:
            try:
                ele = page.ele(sel, timeout=2)
                if ele and ele.states.is_displayed:
                    ele.click()
                    log.info("  已同意协议弹窗")
                    time.sleep(2)
                    break
            except Exception:
                pass

        # 验证处理循环：依次处理 IV 短信验证页 / 登录页或 IV 的 NC 滑块，
        # 直到真正进入登录态或轮次耗尽。IV 引导页(normal_validate)会自动跳到验证页，循环留出时间。
        for _round in range(8):
            if is_seller_logged_in_url(page.url):
                break
            # 协议弹窗可能在跳转后再次出现
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
                # 没有短信表单则尝试 NC 滑块（登录页或 IV 滑块）
                handle_nc_slider(page, max_retry=SLIDER_RETRY, logger=log)
                time.sleep(3)

        # 等待最终跳转（必须真正进入卖家后台等登录态，IV 验证页不算成功）
        for _ in range(15):
            if is_seller_logged_in_url(page.url):
                log.info(f"  登录成功: {page.url}")
                break
            time.sleep(1)

        # 获取 cookies
        if is_seller_logged_in_url(page.url):
            browser_cookies = page.cookies()
            cookies_dict = {c["name"]: c["value"] for c in browser_cookies}
            page.quit()
            return cookies_dict, "success"

        # 仍停留在验证页/登录页：明确区分 IV 二次验证与普通超时，绝不写无效 Cookie
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


def prepare_shop_cookie(
    shop_name: str,
    login_id: str | None = None,
    password: str | None = None,
    db_cookie_str: str | None = None,
    db_cookie: str | dict | list | None = None,
    site: str = DEFAULT_COOKIE_SITE,
    save_local: bool = False,
    **login_options,
) -> dict[str, Any]:
    """
    准备店铺 Cookie：
    1. 先验证数据库已有 Cookie；有效则用该 Cookie 访问后台完成滚动刷新（不重登、不发短信），
       并把刷新后的 Cookie 覆盖写回 get_cookie。
    2. 失效后走纯协议登录（iv8 令牌破 RGV587 + IV 短信自动求解）。
    3. 协议失败再走浏览器自动化兜底（含 IV 验证页短信/滑块处理）。
    4. 登录成功后，写库前再次校验新 Cookie 有效，校验通过才覆盖写入 get_cookie。
    """
    configure_login(
        login_id=login_id,
        password=password,
        timeout=login_options.get("timeout"),
        max_retries=login_options.get("max_retries"),
        retry_delay=login_options.get("retry_delay"),
        slider_retry=login_options.get("slider_retry"),
        validate_url=login_options.get("validate_url"),
        user_agent=login_options.get("user_agent"),
    )

    log.info(f"{shop_name} 开始准备淘宝登录 Cookie，站点={site}")
    if not db_cookie_str and not db_cookie:
        db_cookie_str, db_cookie = load_cookies_database(site, shop_name)

    existing_cookies = merge_cookie_sources(db_cookie_str, db_cookie)
    if existing_cookies:
        log.info(f"{shop_name} 发现数据库 Cookie，先验证有效性")
        # 有效则用该 Cookie 访问后台完成滚动刷新（不重登、不发短信），并把刷新后的 Cookie 覆盖写回
        cookie_valid, refreshed_cookies = validate_and_refresh_cookies(existing_cookies)
        if cookie_valid:
            log.info(f"{shop_name} 数据库 Cookie 有效，刷新后回写 get_cookie（无需重新登录）")
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
                # 刷新回写失败不影响"Cookie 有效"结论，仅记录
                log.warning(f"{shop_name} 刷新 Cookie 回写失败（不影响使用）：{type(exc).__name__}: {exc}")
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

    cookies, status = login_with_retry()
    log.info("=" * 55)
    log.info(f"{shop_name} 登录结果: {status}")

    if status == "success" and cookies:
        # 写库前再次验证新 Cookie 确实有效，校验通过才覆盖写入，避免用无效 Cookie 盖掉数据库
        if not validate_cookies(cookies):
            log.warning(f"{shop_name} 新登录 Cookie 校验未通过，跳过写库以保护数据库已有 Cookie")
            return {
                "shop_name": shop_name,
                "site": site,
                "status": "error:new_cookie_invalid",
                "cookie_count": len(cookies),
                "saved_to_db": False,
            }

        log.info(f"{shop_name} 新登录 Cookie 校验通过，开始覆盖写入 get_cookie")
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


# ═══════════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════════

def main():
    log.info("淘宝卖家后台协议登录")
    log.info(f"  店铺名称: {SHOP_NAME}")
    log.info(f"  登录账号: {LOGIN_ID}")
    log.info(f"  目标: Havana 登录系统")

    result = prepare_shop_cookie(
        shop_name=SHOP_NAME,
        login_id=LOGIN_ID,
        password=PASSWORD,
        site=DEFAULT_COOKIE_SITE,
        save_local=True,
    )
    status = result["status"]

    if status in ("success", "db_cookie_valid"):
        log.info(f"Cookie 准备完成，状态={status}，数量={result.get('cookie_count', 0)}")
    elif status == "captcha":
        log.warning("触发验证码，协议方式无法通过")
        log.warning("建议: 运行 auto_login/taobao_login_auto.py 使用浏览器自动化方案")
    elif status.startswith("need_verify:"):
        log.warning(f"需要额外验证: {status}")
        log.warning("建议: 运行 auto_login/taobao_login_auto.py 使用浏览器自动化方案")
    else:
        log.error(f"登录失败: {status}")


if __name__ == "__main__":
    main()
