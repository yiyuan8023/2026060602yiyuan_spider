# -*- coding: utf-8 -*-
"""快速递归捕获短信验证 UI 选择器（仅淘宝登录相关 frame）。结果实时写 debug_sms_result.txt。"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from DrissionPage import ChromiumPage, ChromiumOptions
from config.local_config import get_local_section

OUT = open(Path(__file__).parent / "debug_sms_result.txt", "w", encoding="utf-8")
def w(msg):
    OUT.write(str(msg) + "\n"); OUT.flush()

sec = get_local_section("dchain_tb_login"); shop = sec["shops"][0]
co = ChromiumOptions(); co.auto_port(True); co.set_argument("--lang=zh-CN")
co.set_argument("--disable-blink-features=AutomationControlled")
page = ChromiumPage(addr_or_opts=co)

KW = ("获取", "验证", "校验", "码", "code", "Code", "短信")
SKIP = ("g.alicdn.com", "xstore", "1688.com", "xdomain", "aplus")

def matches(s):
    s = s or ""
    return any(k in s for k in KW)

def walk(ctx, path, depth=0):
    if depth > 4:
        return
    try:
        for tag in ("button", "a", "input"):
            for e in ctx.eles(f"tag:{tag}"):
                tx = (e.text or "").strip()
                idv = e.attr("id"); nm = e.attr("name"); ph = e.attr("placeholder")
                if matches(tx) or matches(idv) or matches(nm) or matches(ph):
                    w(f"  [{path}] {tag.upper()} text={tx[:24]!r} id={idv!r} name={nm!r} ph={ph!r} class={(e.attr('class') or '')[:36]!r}")
    except Exception as ex:
        w(f"  [{path}] dump err {type(ex).__name__}")
    try:
        for ifr in ctx.eles("tag:iframe"):
            src = (ifr.attr("src") or "")
            if any(s in src for s in SKIP):
                continue
            try:
                fr = ctx.get_frame(ifr)
                if fr:
                    walk(fr, f"{path}>if({src[:36]})", depth + 1)
            except Exception:
                continue
    except Exception:
        pass

def get_login_frame():
    for f in ["xpath://iframe[contains(@src,'login.jhtml')]", "#alibaba-login-box"]:
        fr = page.get_frame(f)
        if fr and fr.eles("tag:input"):
            return fr
    return None

try:
    page.get("https://web.scm.tmall.com/login"); time.sleep(5)
    page.ele("xpath://span[contains(text(),'淘宝登录')]", timeout=4).click(); time.sleep(4)
    ctx = get_login_frame()
    ctx.ele("css:#fm-login-id", timeout=4).input(shop["login_id"]); time.sleep(0.2)
    ctx.ele("css:#fm-login-password", timeout=4).input(shop["password"]); time.sleep(0.2)
    ctx.ele("xpath://button[contains(text(),'登录')]", timeout=3).click()
    w("已点登录，开始扫描（请保持短信界面）...")
    for i in range(14):
        time.sleep(4)
        w(f"=== 扫描 #{i+1} URL={page.url[:55]} ===")
        walk(page, "main")
        if "login" not in page.url.lower():
            w(">>> 已离开登录页: " + page.url); break
    page.get_screenshot(str(Path(__file__).parent / "debug_capture_sms.png"))
    w("DONE")
finally:
    OUT.close()
    try: page.quit()
    except Exception: pass
