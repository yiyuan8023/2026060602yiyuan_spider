#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_security_tokens.py
从淘宝登录页提取 AWSC 安全 token (umidToken + ua)
通过浏览器环境让 AWSC SDK 自然初始化后提取
"""

import time
import json
import logging
from DrissionPage import ChromiumPage, ChromiumOptions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("token_extractor")


def extract_awsc_tokens(wait_max=20, page=None):
    """
    从淘宝登录页提取 AWSC 安全 token

    Args:
        wait_max: 最长等待秒数
        page: 可选，已打开登录页的 ChromiumPage 实例（复用时传入）

    Returns:
        dict: {"umidToken": str, "ua": str, "success": bool}
    """
    own_page = page is None

    try:
        if own_page:
            log.info("启动浏览器提取安全 token...")
            co = ChromiumOptions()
            co.set_argument('--lang=zh-CN')
            co.set_argument('--disable-blink-features=AutomationControlled')
            co.auto_port(True)
            page = ChromiumPage(addr_or_opts=co)
            page.get('https://login.taobao.com/havanaone/login/login.htm?bizName=taobao')
            time.sleep(4)

        # 手动初始化 um 模块并获取 token
        page.run_js('''
            window._secTokens = {umidToken: "", ua: "", ready: false};

            // 获取 UA (bx-ua)
            if (window.baxiaCommon && typeof window.baxiaCommon.getUA === 'function') {
                try { window._secTokens.ua = window.baxiaCommon.getUA(); } catch(e) {}
            }

            // 初始化 um 模块获取 umidToken
            if (window.AWSC && window.AWSC.use) {
                window.AWSC.use("um", function(state, module) {
                    if (state === "loaded" && module && module.init) {
                        module.init({appName: "taobao"}, function(status, data) {
                            if (status === "success" && data && data.tn) {
                                window._secTokens.umidToken = data.tn;
                                window._secTokens.ready = true;
                            }
                        });
                    }
                });
            }
        ''')

        # 等待异步回调完成
        for i in range(int(wait_max / 2)):
            time.sleep(2)
            result = page.run_js('''
                return JSON.stringify(window._secTokens || {});
            ''')
            data = json.loads(result)

            if data.get('ready') and data.get('umidToken'):
                # 再取一次最新 UA
                ua = page.run_js('''
                    if (window.baxiaCommon && typeof window.baxiaCommon.getUA === 'function') {
                        return window.baxiaCommon.getUA();
                    }
                    return window._secTokens.ua || "";
                ''') or data.get('ua', '')

                log.info(f"umidToken: {data['umidToken'][:50]}...")
                log.info(f"ua: {ua[:80]}...")
                return {
                    "success": True,
                    "umidToken": data['umidToken'],
                    "ua": ua,
                }

        log.warning(f"等待 {wait_max}s 未获取到 umidToken")
        return {"success": False, "umidToken": "", "ua": ""}

    except Exception as e:
        log.error(f"提取 token 异常: {e}")
        return {"success": False, "umidToken": "", "ua": ""}
    finally:
        if own_page and page:
            page.quit()


if __name__ == "__main__":
    result = extract_awsc_tokens()
    print("\n" + "="*60)
    print(json.dumps(result, indent=2, ensure_ascii=False))
