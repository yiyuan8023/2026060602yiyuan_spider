#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-20
- 文件用途：纯协议（无浏览器）提取淘系 Havana 登录所需的 AWSC 安全令牌 umidToken 与 bx-ua。
- 业务范围：适用于 API_login/API_TaoXi_login 协议登录，替代 DrissionPage 的 extract_security_tokens 主路径。
- 依赖入口：iv8（C++ 原生浏览器环境）执行 js/awsc_baxia.js、js/um.js、js/collina.js；requests 转发 SDK 网络请求。
- 实现要点：iv8 跑 AWSC SDK 生成设备指纹与行为指纹，SDK 想发的请求经 netLog 截获 → requests 真实发出
  → add_resource 注入响应 → eventLoop 推进；umidToken 直接解析 ynuf um.json 响应的 tn，bx-ua 取 configFY 回调 fy.getUA()。
- 验收方式：单跑本文件断言 umidToken/ua 非空且格式合理；与 DrissionPage 提取结果对照。
- 注意事项：不读账号密码、不写库；日志只输出 token 长度/前缀，不输出完整 token 与完整 Cookie。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

HERE = Path(__file__).resolve().parent
JS_DIR = HERE / "js"
# AWSC SDK 三件套：编排器 + umidToken 模块 + bx-ua(uab/collina) 模块
SDK_FILES = ("awsc_baxia.js", "um.js", "collina.js")

HAVANA_LOGIN_URL = "https://login.taobao.com/havanaone/login/login.htm?bizName=taobao"
UM_TOKEN_URL = "https://ynuf.aliapp.org/service/um.json"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# 补 MessageChannel 桩：AWSC SDK 会检测，iv8 默认未实现
_MESSAGE_CHANNEL_STUB = """
window.MessageChannel = __iv8__.wrapNative(function() {
    var p1 = { onmessage: null }, p2 = { onmessage: null };
    p1.postMessage = function(d){ if(p2.onmessage) setTimeout(function(){p2.onmessage({data:d});},0); };
    p2.postMessage = function(d){ if(p1.onmessage) setTimeout(function(){p1.onmessage({data:d});},0); };
    return { port1: p1, port2: p2 };
}, 'MessageChannel');
"""

# configFY 第一参数是 callback(fy)，fy 携带 getUA()；第二参数是配置
_CONFIG_FY = """
window._fy = null;
window._fyReady = false;
window._fyErr = '';
try {
    window.AWSC.configFY(function(fy){
        window._fy = fy;
        window._fyReady = true;
    }, { appName: 'taobao', bizName: 'taobao' });
} catch (e) {
    window._fyErr = String(e && e.message || e);
}
"""

from extra.logger_ import logger


def _build_environment(user_agent: str) -> dict[str, Any]:
    """构造 iv8 浏览器指纹环境，location 指向 Havana 登录页。"""
    return {
        "location": {
            "href": HAVANA_LOGIN_URL,
            "origin": "https://login.taobao.com",
            "protocol": "https:",
            "host": "login.taobao.com",
            "hostname": "login.taobao.com",
            "port": "",
            "pathname": "/havanaone/login/login.htm",
            "search": "?bizName=taobao",
            "hash": "",
        },
        "navigator": {
            "userAgent": user_agent,
            "platform": "Win32",
            "language": "zh-CN",
            "languages": ["zh-CN", "en-US"],
        },
    }


def _make_session(user_agent: str) -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": user_agent,
        "Referer": HAVANA_LOGIN_URL,
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    })
    return session


def _forward_request(session: requests.Session, entry: dict[str, Any], timeout: int) -> tuple[str, int]:
    """把 SDK 想发的请求用 requests 真实发出。"""
    url = entry.get("url", "")
    method = (entry.get("method") or "GET").upper()
    try:
        if method == "POST":
            resp = session.post(
                url,
                data=entry.get("body", "") or "",
                headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
                timeout=timeout,
            )
        else:
            resp = session.get(url, timeout=timeout)
        return resp.text, resp.status_code or 200
    except requests.RequestException as exc:
        logger.warning(f"  AWSC 请求转发失败: {url[:60]} ({type(exc).__name__})")
        return "", 0


def _run_inject_loop(ctx, session: requests.Session, timeout: int, max_rounds: int) -> dict[str, str]:
    """
    迭代驱动 AWSC SDK 的网络流水线：
    推进事件循环 → 读 netLog 新请求 → requests 真实发出 → add_resource 注入响应 → 再推进。
    返回 {url: response_text}，供上层解析 um.json 的 tn。
    """
    captured: dict[str, str] = {}
    fulfilled: set[str] = set()

    for _round in range(max_rounds):
        ctx.eval("__iv8__.eventLoop.sleep(700)")
        entries = ctx.eval("__iv8__.netLog.entries", to_py=True) or []
        new_entries = [e for e in entries if e.get("url") and e["url"] not in fulfilled]

        # umidToken 一旦拿到响应即可提前结束指纹流水线
        if UM_TOKEN_URL in captured and not new_entries:
            break
        if not new_entries:
            continue

        for entry in new_entries:
            url = entry["url"]
            fulfilled.add(url)
            text, status = _forward_request(session, entry, timeout)
            if not text:
                continue
            captured[url] = text
            inject_ct = "application/json" if "json" in url else "application/javascript"
            try:
                ctx.add_resource(url, text, status if status else 200, {"content-type": inject_ct})
            except Exception as exc:  # iv8 注入异常不应中断整体流程
                logger.warning(f"  注入响应失败: {url[:60]} ({type(exc).__name__})")

    return captured


def _parse_umid_token(captured: dict[str, str]) -> str:
    """从 ynuf um.json 响应解析 umidToken（tn 字段）。"""
    raw = captured.get(UM_TOKEN_URL, "")
    if not raw:
        return ""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return ""
    token = payload.get("tn") or payload.get("id") or ""
    return str(token)


def get_security_tokens_iv8(
    user_agent: str | None = None,
    timeout: int = 15,
    max_rounds: int = 14,
) -> dict[str, Any]:
    """
    纯协议提取 AWSC 安全令牌。

    返回 {"umidToken", "ua", "_cookies", "source"}；任一关键令牌缺失时返回 {}，
    由上层回落 DrissionPage 提取。
    """
    user_agent = user_agent or DEFAULT_USER_AGENT

    missing = [name for name in SDK_FILES if not (JS_DIR / name).exists()]
    if missing:
        logger.warning(f"  iv8 token 提取缺少 SDK 文件: {missing}，跳过 iv8 路径")
        return {}

    try:
        import iv8
    except ImportError:
        logger.warning("  iv8 未安装，跳过 iv8 token 提取")
        return {}

    logger.info("  iv8 提取 AWSC 安全令牌 (umidToken + bx-ua)...")
    session = _make_session(user_agent)
    environment = _build_environment(user_agent)

    try:
        with iv8.JSContext(environment=environment, config={"timezone": "Asia/Shanghai"}) as ctx:
            ctx.eval(_MESSAGE_CHANNEL_STUB)
            # 必须 page.load 初始化资源 bundle，否则 add_resource 不可用
            ctx.expose(
                {"baseURL": HAVANA_LOGIN_URL,
                 "html": "<html><head></head><body></body></html>",
                 "resources": {}},
                "snapshot",
            )
            ctx.eval("__iv8__.page.load(__iv8__.data.snapshot)")
            ctx.eval("__iv8__.eventLoop.sleep(50)")

            for name in SDK_FILES:
                code = (JS_DIR / name).read_text(encoding="utf-8", errors="replace")
                ctx.eval(code, name=f"https://g.alicdn.com/AWSC/{name}")

            ctx.eval(_CONFIG_FY)
            fy_err = ctx.eval("window._fyErr") or ""
            if fy_err:
                logger.warning(f"  configFY 初始化异常: {fy_err[:80]}")

            captured = _run_inject_loop(ctx, session, timeout=timeout, max_rounds=max_rounds)
            ctx.eval("__iv8__.eventLoop.sleep(800)")

            umid_token = _parse_umid_token(captured)
            try:
                ua_val = ctx.eval(
                    "(window._fy && typeof window._fy.getUA==='function') ? String(window._fy.getUA()) : ''"
                ) or ""
            except Exception:
                ua_val = ""
    except Exception as exc:
        logger.warning(f"  iv8 token 提取失败: {type(exc).__name__}: {exc}")
        return {}

    # bx-ua 正常以 "<数字>#" 开头（如 140#...）；哨兵值 default*/defaultUA* 视为无效
    ua_valid = bool(ua_val) and "#" in ua_val[:6] and not ua_val.lower().startswith("default")
    if not umid_token or not ua_valid:
        logger.warning(
            f"  iv8 token 不完整 (umid={'有' if umid_token else '空'}, "
            f"ua={'有' if ua_valid else '空'})，将回落浏览器提取"
        )
        return {}

    # inject 过程中 session 已从真实请求积累到部分淘宝 Cookie（cna 等），一并带回登录会话
    cookies = {name: value for name, value in session.cookies.get_dict().items()}

    logger.info(f"  iv8 令牌就绪: umidToken({len(umid_token)}位 {umid_token[:8]}…), "
             f"bx-ua({len(ua_val)}位 {ua_val[:6]}…), cookies={len(cookies)}")
    return {
        "umidToken": umid_token,
        "ua": ua_val,
        "_cookies": cookies,
        "source": "iv8",
    }


if __name__ == "__main__":
    result = get_security_tokens_iv8()
    print("\n" + "=" * 60)
    if result:
        print("umidToken 长度:", len(result["umidToken"]), "前缀:", result["umidToken"][:16])
        print("bx-ua 长度:", len(result["ua"]), "前缀:", result["ua"][:24])
        print("session cookies:", list(result["_cookies"].keys())[:12])
        print("source:", result["source"])
    else:
        print("iv8 令牌提取失败（返回空，应回落 DrissionPage）")
