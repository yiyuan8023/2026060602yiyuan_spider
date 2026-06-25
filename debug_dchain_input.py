# -*- coding: utf-8 -*-
"""调试：DChain 淘宝登录 tab 的 iframe / 输入框结构与填充。仅诊断，不提交登录。"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from DrissionPage import ChromiumPage, ChromiumOptions

LOGIN_URL = "https://web.scm.tmall.com/login"

co = ChromiumOptions()
co.auto_port(True)
co.set_argument("--lang=zh-CN")
co.set_argument("--disable-blink-features=AutomationControlled")
co.set_pref("credentials_enable_service", False)
co.set_pref("profile.password_manager_enabled", False)
# 非 headless，便于真实渲染（看不到窗口也无妨，行为更接近真人）

page = ChromiumPage(addr_or_opts=co)
try:
    page.get(LOGIN_URL)
    time.sleep(5)
    print("URL:", page.url)
    print("title:", page.title)

    def dump_iframes(tag):
        ifrs = page.eles("tag:iframe")
        print(f"[{tag}] iframe 数量 = {len(ifrs)}")
        for i, f in enumerate(ifrs):
            try:
                print(f"   #{i} id={f.attr('id')!r} name={f.attr('name')!r} src={(f.attr('src') or '')[:70]!r}")
            except Exception as e:
                print(f"   #{i} <读取失败 {type(e).__name__}>")

    dump_iframes("初始")

    # 切淘宝登录 tab
    for sel in ["xpath://span[contains(text(),'淘宝登录')]",
                "xpath://*[contains(text(),'淘宝登录')]",
                "xpath://div[contains(text(),'淘宝登录')]"]:
        try:
            tab = page.ele(sel, timeout=3)
            if tab:
                print(f"找到淘宝登录tab: {sel} -> 文本={tab.text!r}")
                tab.click()
                time.sleep(4)
                break
        except Exception as e:
            print(f"  tab {sel} 失败 {type(e).__name__}")

    dump_iframes("切tab后")

    # 尝试进入登录 iframe 并枚举 input
    frame = None
    for fid in ["#alibaba-login-box", 0, 1]:
        try:
            fr = page.get_frame(fid)
            if fr:
                inputs = fr.eles("tag:input")
                print(f"get_frame({fid!r}) ok, input 数量={len(inputs)}")
                if inputs:
                    frame = fr
                    for j, inp in enumerate(inputs):
                        print(f"     input#{j} id={inp.attr('id')!r} name={inp.attr('name')!r} "
                              f"type={inp.attr('type')!r} placeholder={inp.attr('placeholder')!r}")
                    break
        except Exception as e:
            print(f"get_frame({fid!r}) 失败 {type(e).__name__}: {e}")

    if not frame:
        print("!! 未能进入含 input 的登录 iframe")
        page.get_screenshot(str(Path(__file__).parent / "debug_dchain_noframe.png"))
        page.quit(); sys.exit(0)

    # 定位账号框，试多种填充
    login_input = None
    for sel in ["css:#fm-login-id", "css:input[name='fm-login-id']",
                "css:input[placeholder*='账号']", "css:input[placeholder*='会员']",
                "css:input[placeholder*='邮箱']", "css:input[placeholder*='手机']"]:
        try:
            e = frame.ele(sel, timeout=2)
            if e:
                login_input = e
                print(f"账号框命中: {sel}")
                break
        except Exception:
            pass

    if not login_input:
        print("!! 账号框未命中")
        page.quit(); sys.exit(0)

    test_val = "TEST_ACCOUNT_123"
    print("\n--- 方式1: clear + input ---")
    try:
        login_input.click(); time.sleep(0.3)
        login_input.clear(); time.sleep(0.2)
        login_input.input(test_val); time.sleep(0.5)
        print("  回读 value =", repr(login_input.attr("value")))
    except Exception as e:
        print("  方式1异常", type(e).__name__, e)

    print("--- 方式2: JS 直接 set value + dispatch input/change ---")
    try:
        frame.run_js(
            "arguments[0].value=arguments[1];"
            "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
            "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
            login_input, "JS_SET_456")
        time.sleep(0.4)
        print("  回读 value =", repr(login_input.attr("value")))
    except Exception as e:
        print("  方式2异常", type(e).__name__, e)

    print("--- 方式3: focus + 逐字符 ---")
    try:
        login_input.clear()
        frame.run_js("arguments[0].focus();", login_input)
        for ch in "CHAR_789":
            login_input.input(ch); time.sleep(0.05)
        time.sleep(0.3)
        print("  回读 value =", repr(login_input.attr("value")))
    except Exception as e:
        print("  方式3异常", type(e).__name__, e)

    page.get_screenshot(str(Path(__file__).parent / "debug_dchain_filled.png"))
    print("\n截图已存 debug_dchain_filled.png")
finally:
    try:
        page.quit()
    except Exception:
        pass
