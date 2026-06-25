# -*- coding: utf-8 -*-
"""验证 browser_fallback 的 iframe 选择 + 真实账号填充，只填不提交（不触发登录/风控）。"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from DrissionPage import ChromiumPage, ChromiumOptions
from config.local_config import get_local_section
from API_login.API_TaoXi_login.API_TaoXi_base_login import browser_fallback as bf

sec = get_local_section("dchain_tb_login"); shop = sec["shops"][0]
LOGIN_ID = shop["login_id"]; PASSWORD = shop["password"]

co = ChromiumOptions(); co.auto_port(True)
co.set_argument("--lang=zh-CN"); co.set_argument("--disable-blink-features=AutomationControlled")
page = ChromiumPage(addr_or_opts=co)
try:
    page.get("https://web.scm.tmall.com/login"); time.sleep(5)
    tab = page.ele("xpath://span[contains(text(),'淘宝登录')]", timeout=4)
    if tab:
        tab.click(); time.sleep(4); print("已切到淘宝登录 tab")

    # 复用与 browser_fallback 相同的 iframe 选择逻辑
    ctx = page
    for floc in ["xpath://iframe[contains(@src,'login.jhtml')]",
                 "xpath://iframe[contains(@src,'login.taobao.com/member')]",
                 "#alibaba-login-box"]:
        fr = page.get_frame(floc)
        if fr and fr.eles("tag:input"):
            ctx = fr; print(f"进入 iframe: {floc}"); break

    login_input = ctx.ele("css:#fm-login-id", timeout=4)
    login_input.click(); time.sleep(0.2); login_input.clear(); login_input.input(LOGIN_ID); time.sleep(0.4)
    v1 = bf._read_input_value(ctx, login_input)
    if not v1:
        bf._js_set_value(ctx, login_input, LOGIN_ID); v1 = bf._read_input_value(ctx, login_input)

    pwd_input = ctx.ele("css:#fm-login-password", timeout=4)
    pwd_input.clear(); pwd_input.input(PASSWORD); time.sleep(0.3)
    v2 = bf._read_input_value(ctx, pwd_input)
    if not v2:
        bf._js_set_value(ctx, pwd_input, PASSWORD); v2 = bf._read_input_value(ctx, pwd_input)

    print(f"账号框回读: {v1!r}")
    print(f"密码框回读: 长度={len(v2)} (非空={bool(v2)})")
    page.get_screenshot(str(Path(__file__).parent / "debug_dchain_fill_only.png"))
    print("截图: debug_dchain_fill_only.png  （未点击登录，未提交）")
finally:
    try: page.quit()
    except Exception: pass
