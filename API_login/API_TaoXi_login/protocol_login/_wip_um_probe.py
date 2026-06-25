# -*- coding: utf-8 -*-
"""Phase3：§9 Proxy 探测 um.init 超时卡点——记录缺失 API 访问 + JS 错误 + netLog。"""
import sys, json
from pathlib import Path
sys.path.insert(0, "F:/05ai_project/2026060602yiyuan_spider")
import iv8, requests
from API_login.API_TaoXi_login.protocol_login import iv8_token_provider as P

JS = Path(__file__).resolve().parent / "js_live"
UA = P.DEFAULT_USER_AGENT
PAGE = "https://login.taobao.com/member/login.jhtml?style=miniall&sub=true&from=ascp"
ENC = "090D1F110F187839282B151408"
MODULES = {
    "https://g.alicdn.com/AWSC/AWSC/awsc.js": "AWSC_AWSC_awsc.js",
    "https://g.alicdn.com/sd/baxia/2.5.36/baxiaCommon.js": "sd_baxia_2.5.36_baxiaCommon.js",
    "https://g.alicdn.com/AWSC/et/1.84.2/et_f.js": "AWSC_et_1.84.2_et_f.js",
    "https://g.alicdn.com/AWSC/uab/1.140.0/collina.js": "AWSC_uab_1.140.0_collina.js",
    "https://g.alicdn.com/AWSC/WebUMID/1.93.0/um.js": "AWSC_WebUMID_1.93.0_um.js",
    "https://g.alicdn.com/AWSC/fireyejs/1.234.24/fireyejs.js": "AWSC_fireyejs_1.234.24_fireyejs.js",
    "https://g.alicdn.com/secdev/sufei_data/3.9.14/index.js": "secdev_sufei_data_3.9.14_index.js",
}
env = {"location": {"href": PAGE, "origin": "https://login.taobao.com", "protocol": "https:",
                    "host": "login.taobao.com", "hostname": "login.taobao.com", "port": "",
                    "pathname": "/member/login.jhtml", "search": "?style=miniall&sub=true&from=ascp", "hash": ""},
       "navigator": {"userAgent": UA, "platform": "Win32", "language": "zh-CN", "languages": ["zh-CN", "en-US"]}}
session = requests.Session(); session.headers.update({"User-Agent": UA, "Referer": PAGE})

with iv8.JSContext(environment=env, config={"timezone": "Asia/Shanghai"}) as ctx:
    ctx.eval(P._MESSAGE_CHANNEL_STUB)
    ctx.expose({"baseURL": PAGE, "html": "<html><head></head><body></body></html>", "resources": {}}, "snapshot")
    ctx.eval("__iv8__.page.load(__iv8__.data.snapshot)")
    ctx.eval("__iv8__.eventLoop.sleep(50)")
    for url, fn in MODULES.items():
        ctx.add_resource(url, (JS / fn).read_text(encoding="utf-8", errors="replace"), 200,
                         {"content-type": "application/javascript"})

    # 错误捕获 + 缺失 API 记录（§9.2.2 思路，温和版：只记录不替换 window）
    ctx.eval("""
        window.__missing__ = []; window.__errs__ = []; window.__calls__=[];
        window.addEventListener && window.addEventListener('error', function(e){ window.__errs__.push('ERR '+(e.message||e)); });
        window.addEventListener && window.addEventListener('unhandledrejection', function(e){ window.__errs__.push('REJ '+(e.reason && e.reason.message || e.reason)); });
        ['requestIdleCallback','requestAnimationFrame','Worker','SharedWorker','BroadcastChannel',
         'OffscreenCanvas','createImageBitmap','queueMicrotask','reportError'].forEach(function(k){
            window.__calls__.push(k+'='+(typeof window[k]));
        });
        ['mediaDevices','permissions','connection','getBattery','hardwareConcurrency','deviceMemory',
         'plugins','webdriver','userAgentData','sendBeacon'].forEach(function(k){
            window.__calls__.push('nav.'+k+'='+(typeof navigator[k]));
        });
    """)
    # 直接按依赖顺序 eval 每个模块（同步注册，避免 AWSC.use 动态加载超时）
    EVAL_ORDER = [
        ("AWSC_AWSC_awsc.js", "https://g.alicdn.com/AWSC/AWSC/awsc.js"),
        ("sd_baxia_2.5.36_baxiaCommon.js", "https://g.alicdn.com/sd/baxia/2.5.36/baxiaCommon.js"),
        ("AWSC_et_1.84.2_et_f.js", "https://g.alicdn.com/AWSC/et/1.84.2/et_f.js"),
        ("AWSC_uab_1.140.0_collina.js", "https://g.alicdn.com/AWSC/uab/1.140.0/collina.js"),
        ("AWSC_WebUMID_1.93.0_um.js", "https://g.alicdn.com/AWSC/WebUMID/1.93.0/um.js"),
        ("AWSC_fireyejs_1.234.24_fireyejs.js", "https://g.alicdn.com/AWSC/fireyejs/1.234.24/fireyejs.js"),
        ("secdev_sufei_data_3.9.14_index.js", "https://g.alicdn.com/secdev/sufei_data/3.9.14/index.js"),
    ]
    for fn, nm in EVAL_ORDER:
        try:
            ctx.eval((JS / fn).read_text(encoding="utf-8", errors="replace"), name=nm)
        except Exception as ex:
            print(f"  eval {fn} FAILED: {type(ex).__name__}: {str(ex)[:120]}")
    ctx.eval("__iv8__.eventLoop.sleep(300)")
    print("AWSC.use 类型:", ctx.eval("typeof (window.AWSC && window.AWSC.use)"))

    ctx.eval(f"""
        window._umState='start'; window._umErr='';
        try {{
            window.AWSC.use("um", function(state, mod){{
                window._umState='use:'+state;
                if (state==='loaded' && mod && mod.init) {{
                    window._umState='init-called';
                    window._umMod = mod;
                    mod.init({{appName: "{ENC}"}}, function(s, data){{
                        window._umState='cb:'+s;
                        try {{ window._umData = JSON.stringify(data); }} catch(e){{ window._umData='<'+typeof data+'>'; }}
                        if (data && data.tn) window._umTn=String(data.tn);
                    }});
                }}
            }});
        }} catch(e){{ window._umErr=String(e&&e.message||e); }}
    """)
    # 自定义注入循环：按条目顺序转发（不按 URL 去重），让 repTw 重试都能拿到响应
    processed = 0
    for _r in range(30):
        ctx.eval("__iv8__.eventLoop.sleep(500)")
        entries = ctx.eval("__iv8__.netLog.entries", to_py=True) or []
        new = entries[processed:]
        processed = len(entries)
        for entry in new:
            url = entry.get("url", "")
            if not url:
                continue
            text, status = P._forward_request(session, entry, 15)
            if not text:
                continue
            ct = "application/json" if "json" in url else "application/javascript"
            try:
                ctx.add_resource(url, text, status or 200, {"content-type": ct})
            except Exception:
                pass
        if ctx.eval("window._umState && window._umState.indexOf('cb:')===0") and "repWd" in " ".join(e.get("url","") for e in entries):
            break
    ctx.eval("__iv8__.eventLoop.sleep(2000)")

    print("um 最终状态:", ctx.eval("window._umState"), "| umErr:", ctx.eval("window._umErr"))
    print("umidToken(tn):", (ctx.eval("window._umTn") or "(无)")[:40])
    print("um init data:", str(ctx.eval("window._umData") or "(无)")[:300])
    # 尝试从 um 模块直接取 token
    for expr in ("window._umMod && window._umMod.getToken && String(window._umMod.getToken())",
                 "window._umMod && window._umMod.tn && String(window._umMod.tn)",
                 "window.AWSC && AWSC.um && AWSC.um.getToken && String(AWSC.um.getToken())"):
        try:
            v = ctx.eval(expr)
            if v: print(f"  token via [{expr[:40]}...]: {str(v)[:40]}")
        except Exception:
            pass
    # 取 bx-ua（configFY getUA）
    ctx.eval("""
        window._bxua='';
        try { window.AWSC.configFY(function(fy){ try{ window._bxua=String(fy.getUA()); }catch(e){} },
                                    {appName:'ascp', bizName:'ascp'}); } catch(e){ window._bxErr=String(e); }
    """)
    P._run_inject_loop(ctx, session, timeout=10, max_rounds=8)
    ctx.eval("__iv8__.eventLoop.sleep(500)")
    bxua = ctx.eval("window._bxua") or ""
    print("bx-ua:", f"长度={len(bxua)} 前缀={bxua[:8]!r}")
    print("session cookies:", list(session.cookies.get_dict().keys()))
    print("\n=== 关键 API 可用性 ===")
    for c in (ctx.eval("window.__calls__", to_py=True) or []):
        print("  ", c)
    print("\n=== JS 错误 ===")
    for e in (ctx.eval("window.__errs__", to_py=True) or [])[:20]:
        print("  ", str(e)[:160])
    entries = ctx.eval("__iv8__.netLog.entries", to_py=True) or []
    print(f"\n=== netLog {len(entries)} ===")
    for e in entries:
        print(f"  [{e.get('method','GET')}] {(e.get('url') or '')[:90]}")
