# 淘宝 Havana 协议登录逆向实战总结

## 目标

将淘宝卖家后台登录从浏览器自动化还原为纯协议级请求，实现无人值守自动登录闭环。

## 最终交付架构（2026-06 更新：iv8 纯协议 + IV 短信）

```
iv8 生成 umidToken+bx-ua（~4s，无浏览器）
  → 协议 POST login.do（破 RGV587）
  → 若 IV 二次验证：协议短信求解（send_code → 邮箱读码 → 提交 J_Form）
  → 校验登录态 → 写 get_cookie
```

全程**零浏览器、全自动**。低风险账号直接成功；高风险账号走 IV 短信自动过验。

### 关键认知修正

- **RGV587 的真因是 umidToken/bx-ua 缺失或弱**（旧 headless 提取常产弱令牌）。改用 **iv8 执行 JSVMP 的 um.js/collina.js** 生成合格令牌后，初始登录直接放行，**不再出登录页滑块**。
- **真正的拦路是 IV 二次身份验证**（`loginResult` 为空 + 跳 `passport.taobao.com/iv/...`）。实测淘宝**默认下发短信验证**（`identity_verify.htm`，非滑块），用 `iv_sms_solver` 纯协议求解。
- iv8（C++ 原生 200+ 浏览器 API 的真 V8）能跑通 um.js/collina.js 这类 **JSVMP + Canvas/WebGL 依赖**的脚本——这正是旧结论"无法脱浏览器"的突破口。

### iv8 令牌生成配方（已验证）

1. `page.load` 空页（初始化资源 bundle，否则 add_resource 不可用）+ `wrapNative` 补 MessageChannel。
2. eval `awsc_baxia.js` + `um.js` + `collina.js`。
3. `AWSC.configFY(callback, {appName:'taobao', bizName:'taobao'})`——**第一参数是回调 `fn(fy)`**。
4. 注入循环：`netLog` 截获 SDK 请求（et_f.js/wu.json/um.json）→ requests 真实发出 → `add_resource` 注入 → `eventLoop.sleep` 推进。
5. **umidToken = 解析 `ynuf.aliapp.org/service/um.json` 响应的 `tn`**；**bx-ua = `fy.getUA()`**（`140#` 开头）。

### IV 短信求解链路（已验证）

`login_check.htm → normal_validate.htm（pointman 引导，_umidfg=1 即可）→ verify_modes.htm → identity_verify.htm（短信表单）`。
注意：**只能遍历一次**，发码与提交共用同一 htoken，重复遍历会刷新 htoken 导致 `expired.htm`。
提交字段：`_fm.v._0.ph`=验证码、`_fm.v._0.p`=掩码手机、`_fm.v._0.h`=htoken、`_tb_token_` 等。成功跳 `havanaone/login/continue.htm`。

---

## 历史方案（旧版，已被上方 iv8 方案取代）

```
token 提取（headless, ~8s）→ 协议 POST 登录（~4s）→ 重定向拿 Cookie（~2s）
```

总耗时 ~14s，全自动，无需可视浏览器。

---

## 关键技术突破

### 1. 风控卡点定位

协议登录 POST 到 `/havanaone/loginLegacy/password/login.do` 时，缺少两个安全字段导致 `RGV587_ERROR`：

| 字段 | 作用 | 来源 |
|------|------|------|
| `umidToken` | UMID 设备指纹 | AWSC um 模块 → ynuf.aliapp.org |
| `ua` (bx-ua) | 行为指纹 | AWSC uab 模块 (collina.js) |

### 2. AWSC SDK 架构还原

```
baxiaCommon.js (orchestrator)
├── AWSC.use("um")   → g.alicdn.com/AWSC/WebUMID/1.93.0/um.js    → umidToken
├── AWSC.use("uab")  → g.alicdn.com/AWSC/uab/1.140.0/collina.js  → ua (bx-ua)
├── AWSC.use("fy")   → g.alicdn.com/AWSC/fireyejs/1.234.24/fireyejs.js
└── AWSC.use("nc")   → g.alicdn.com/AWSC/nc/1.97.0/nc.js         → 滑块验证
```

模块加载配置在 `g_moduleConfig` 对象中，CDN base 为 `https://g.alicdn.com/`。

### 3. umidToken 生成机制

um.js 是 JSVMP 重混淆（虚拟机保护），无法在 Node.js 中直接运行。其工作流程：

1. 采集设备指纹（Canvas、WebGL、字体、屏幕、时区等）
2. 将指纹数据 POST 到 `ynuf.aliapp.org/service/um.json`
3. 服务端返回 `{id: "T2gA..."}` 即为 umidToken

### 4. Token 提取方案

放弃纯协议提取（um.js JSVMP 无法脱浏览器），采用 **headless 浏览器 + 手动触发初始化**：

```python
# 关键代码：手动触发 AWSC um 模块初始化
page.run_js("""
    window._extractedUmid = '';
    AWSC.use('um', function(state, module) {
        if (state === 'loaded' && module && module.init) {
            module.init({appName: 'taobao'}, function(status, data) {
                if (status === 'success') {
                    window._extractedUmid = data.tn;
                }
            });
        }
    });
""")
```

页面自身的 havana-nlogin 不会主动调用 `AWSC.configFY`（需要用户交互触发），所以必须手动 `AWSC.use("um", ...)` 并调用 `module.init()`。

### 5. UA (bx-ua) 提取

```python
ua = page.run_js("return window.baxiaCommon && window.baxiaCommon.getUA ? baxiaCommon.getUA() : ''")
```

uab 模块自动初始化，无需手动触发，页面加载后即可调用 `getUA()`。

---

## 协议登录完整流程

```
1. headless 打开登录页 → 等待 AWSC SDK 加载
2. 手动 AWSC.use("um") + module.init() → 拿到 umidToken
3. baxiaCommon.getUA() → 拿到 ua
4. 提取浏览器 cookies（含安全 SDK 写入的 cna、cookie2 等）
5. 关闭浏览器
6. HTTP GET 登录页 → 提取 viewConfig（RSA 密钥、API 路径、CSRF）
7. RSA PKCS1_v1.5 加密密码
8. HTTP POST login.do（携带 umidToken + ua + 加密密码 + CSRF）
9. 解析响应：loginResult=success → 跟随 redirectUrl
10. 访问 asyncUrls（跨域写 Cookie）
11. 保存完整 Cookie
```

## 踩坑记录

| 问题 | 原因 | 解决 |
|------|------|------|
| `RGV587_ERROR` 风控 | umidToken/ua 为空 | headless 提取 AWSC token |
| um.js 无法 Node.js 运行 | JSVMP 混淆 + Canvas/WebGL 依赖 | 放弃纯 Node，用 headless |
| `configFY` 调用无效 | 页面未完成初始化 | 直接 `AWSC.use("um")` 拿模块手动 init |
| `baxiaCommon.getUmidToken` undefined | baxiaCommon 对象结构与预期不同 | 改用 `AWSC.use("um")` 回调方式 |
| `redirect` 字段是布尔值 | Havana API 返回 `redirect: true` + `redirectUrl: "..."` | 优先取 `redirectUrl` 字段 |
| headless 模式 umid 为空 | headless 下部分指纹采集异常 | 非 headless 模式提取（或忽略，实测 headless 也能成功） |
| 浏览器 cookie 未注入 protocol session | session.cookies 域名不匹配 | 显式设置 `domain=".taobao.com"` |

## 方法论提炼

1. **风控系统的本质是设备身份验证** — 不是"密码对不对"，而是"你是不是一台合法的浏览器设备"
2. **JSVMP 保护的 JS 不要试图在 Node.js 里跑** — 成本极高，优先用 headless 提取结果
3. **SDK 初始化时机很关键** — 页面加载 ≠ SDK 初始化完成，需要显式触发或等待回调
4. **混合方案是务实选择** — token 生成用浏览器（不可避免），登录用协议（快速可靠）
5. **先证据后结论** — 通过 `AWSC.use()` 回调确认模块状态，不猜测

## 可复用组件

| 文件 | 用途 |
|------|------|
| `extract_security_tokens.py` | AWSC token 提取器（umidToken + ua） |
| `sms_helper.py` | 邮箱 IMAP 轮询短信验证码 |
| `taobao_login.py` | 统一入口：协议登录 + 浏览器降级 |
| `taobao_login_auto.py` | 纯浏览器自动化方案（备用） |

## 适用场景

- 淘宝/天猫卖家后台自动登录
- 阿里系平台（1688、AliExpress）类似 Havana 登录系统
- 任何使用 AWSC/baxia 风控 SDK 的阿里业务线
