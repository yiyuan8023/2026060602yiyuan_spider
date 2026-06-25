# -*- coding: utf-8 -*-
"""Phase2-2：iv8 里跑线上整套 AWSC SDK（awsc.js 加载器 + 各模块预注入），
用加密 appName 初始化 umid，看是否触发 umdcv4 设备注册。"""
import sys, json
from pathlib import Path
sys.path.insert(0, "F:/05ai_project/2026060602yiyuan_spider")
import iv8
import requests
from API_login.API_TaoXi_login.protocol_login import iv8_token_provider as P

JS = Path("F:/05ai_project/2026060602yiyuan_spider/API_login/API_TaoXi_login/protocol_login/js_live")
UA = P.DEFAULT_USER_AGENT
PAGE = "https://login.taobao.com/member/login.jhtml?style=miniall&sub=true&from=ascp"
ENC_APPNAME = "090D1F110F187839282B151408"

# 线上模块 URL -> 本地文件
MODULES = {
    "https://g.alicdn.com/AWSC/AWSC/awsc.js": "AWSC_AWSC_awsc.js",
    "https://g.alicdn.com/sd/baxia/2.5.36/baxiaCommon.js": "sd_baxia_2.5.36_baxiaCommon.js",
    "https://g.alicdn.com/AWSC/et/1.84.2/et_f.js": "AWSC_et_1.84.2_et_f.js",
    "https://g.alicdn.com/AWSC/uab/1.140.0/collina.js": "AWSC_uab_1.140.0_collina.js",
    "https://g.alicdn.com/AWSC/WebUMID/1.93.0/um.js": "AWSC_WebUMID_1.93.0_um.js",
    "https://g.alicdn.com/AWSC/fireyejs/1.234.24/fireyejs.js": "AWSC_fireyejs_1.234.24_fireyejs.js",
    "https://g.alicdn.com/secdev/sufei_data/3.9.14/index.js": "secdev_sufei_data_3.9.14_index.js",
}

env = {
    "location": {"href": PAGE, "origin": "https://login.taobao.com", "protocol": "https:",
                 "host": "login.taobao.com", "hostname": "login.taobao.com", "port": "",
                 "pathname": "/member/login.jhtml", "search": "?style=miniall&sub=true&from=ascp", "hash": ""},
    "navigator": {"userAgent": UA, "platform": "Win32", "language": "zh-CN", "languages": ["zh-CN", "en-US"]},
}
session = requests.Session(); session.headers.update({"User-Agent": UA, "Referer": PAGE})

with iv8.JSContext(environment=env, config={"timezone": "Asia/Shanghai"}) as ctx:
    ctx.eval(P._MESSAGE_CHANNEL_STUB)
    ctx.expose({"baseURL": PAGE, "html": "<html><head></head><body></body></html>", "resources": {}}, "snapshot")
    ctx.eval("__iv8__.page.load(__iv8__.data.snapshot)")
    ctx.eval("__iv8__.eventLoop.sleep(50)")

    # 预注入所有模块资源（AWSC.use 动态 <script> 加载时命中）
    for url, fn in MODULES.items():
        code = (JS / fn).read_text(encoding="utf-8", errors="replace")
        ctx.add_resource(url, code, 200, {"content-type": "application/javascript"})

    # 先加载 AWSC 框架
    awsc_code = (JS / "AWSC_AWSC_awsc.js").read_text(encoding="utf-8", errors="replace")
    ctx.eval(awsc_code, name="https://g.alicdn.com/AWSC/AWSC/awsc.js")
    ctx.eval("__iv8__.eventLoop.sleep(200)")
    print("AWSC 存在:", ctx.eval("typeof window.AWSC"))

    # 初始化 umid（尝试加密 appName）
    ctx.eval(f"""
        window._umState=''; window._umErr=''; window._umTn='';
        try {{
            window.AWSC.use("um", function(state, mod){{
                window._umState = state;
                if (state==='loaded' && mod && mod.init) {{
                    mod.init({{appName: "{ENC_APPNAME}", ucp:1}}, function(s, data){{
                        window._umState='init:'+s;
                        if (data && data.tn) window._umTn = String(data.tn);
                    }});
                }}
            }});
        }} catch(e){{ window._umErr=String(e&&e.message||e); }}
    """)

    captured = P._run_inject_loop(ctx, session, timeout=15, max_rounds=24)
    ctx.eval("__iv8__.eventLoop.sleep(800)")

    print("um 状态:", ctx.eval("window._umState"), "| err:", ctx.eval("window._umErr"))
    print("um tn:", (ctx.eval("window._umTn") or "(无)")[:24])
    entries = ctx.eval("__iv8__.netLog.entries", to_py=True) or []
    print(f"\n==== netLog {len(entries)} 个请求 ====")
    for e in entries:
        print(f"  [{e.get('method','GET')}] {(e.get('url') or '')[:100]}")
    urls = " ".join(e.get("url", "") for e in entries)
    print("\n含 umdcv4:", "umdcv4" in urls, "| repTw:", "repTw" in urls, "| repWd:", "repWd" in urls)
