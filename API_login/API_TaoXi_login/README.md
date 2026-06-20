# 淘系登录 Cookie 准备模块

本目录是 `yiyuan_spider` 项目内的淘系登录 API 模块，用于为生意参谋/淘宝卖家后台准备可复用 Cookie。模块不单独维护 Git 仓库、不单独维护虚拟环境，统一使用项目根目录的 `.venv`、`config/local.json`、`database` 和 `extra.logger_`。

## 当前定位

- API 层：`API_login/API_TaoXi_login/taobao_login.py`
- 启动脚本：`jobs_login/taobao_shop_cookie.py`
- 配置文件：`config/local.json`
- 配置示例：`config/local.example.json`
- Cookie 读取面：数据库 `cookie` 视图/表
- Cookie 写入面：数据库 `get_cookie`

## 登录链路

当前执行顺序是：

1. 从 `config/local.json` 读取 `taobao_login` 多店铺配置。
2. 每个店铺先通过 `select_shop_date(table_name, site, [shop_name], recent_days)` 读取数据库已有 Cookie。
3. `prepare_shop_cookie()` 先验证数据库 Cookie 是否仍可用；**有效则用该 Cookie 访问后台完成滚动刷新（捕获服务端 Set-Cookie，滑动续期 + 轮转令牌更新），把刷新后的 Cookie 覆盖写回 `get_cookie`，不重登、不发短信**。
4. Cookie 失效或不存在时，才走纯协议登录。
5. 协议登录先提取 AWSC 安全令牌 `umidToken` 与 `bx-ua`：优先用 **iv8（C++ 原生浏览器环境）执行 `protocol_login/js/` 下 `awsc_baxia.js`+`um.js`+`collina.js` 纯协议生成**（无浏览器，~4 秒），iv8 不可用时回落 DrissionPage 提取。合格令牌可直接通过初始 `RGV587` 风控。
6. 若平台返回 IV 二次身份验证（`loginResult` 为空且跳转 `passport.taobao.com/iv/...`），调用 `iv_sms_solver` 纯协议求解：发码 `send_code.do` → `sms_helper` 读邮箱转发验证码 → 提交 `J_Form` 过 IV。
7. 登录/IV 通过后补全 `asyncUrls`、校验登录态有效，再写入 `get_cookie`。
8. 纯协议（含 IV 短信）失败时，降级到浏览器自动化兜底；兜底严格判定登录态，IV 验证页不会被误判为成功。
9. 单个店铺失败时记录日志、发送钉钉通知，并继续执行下一个店铺。

## 配置格式

`config/local.json` 中使用 `taobao_login` 段配置，不再支持旧字段 `account` / `sub_name`，必须直接配置完整 `login_id`。

```json
{
  "taobao_login": {
    "table_name": "get_cookie",
    "site": "生意参谋",
    "recent_days": 1,
    "manual_timeout": 300,
    "defaults": {
      "timeout": 30,
      "max_retries": 3,
      "retry_delay": 5,
      "slider_retry": 4,
      "validate_url": "https://myseller.taobao.com/home.htm",
      "user_agent": "Mozilla/5.0 ..."
    },
    "shops": [
      {
        "shop_name": "示例店铺",
        "login_id": "主账号:子账号",
        "password": "登录密码"
      }
    ]
  }
}
```

说明：

- `shop_name` 是数据库 Cookie 按店铺查询和写入时使用的店铺名。
- `login_id` 是淘宝登录页使用的完整登录账号，例如 `主账号:子账号`。
- `password` 是该登录账号对应的密码。
- `site` 当前统一使用 `生意参谋`。
- `source_site` / `target_site` 已合并为 `site`。

## 钉钉通知

单店铺失败时会调用项目已有钉钉通知模块。需要在 `config/local.json` 中配置：

```json
{
  "dingtalk": {
    "robot_webhook": "钉钉机器人 Webhook",
    "robot_secret": "",
    "notify_enabled": true,
    "notify_keyword": "机器人关键词",
    "notify_at_mobiles": [],
    "notify_is_at_all": false,
    "notify_use_card": false
  }
}
```

注意：

- 如果钉钉机器人开启了“关键词”安全策略，必须配置 `notify_keyword`。
- 如果机器人开启了“加签”，必须配置 `robot_secret`。
- 通知正文只包含脚本、站点、店铺、目标表和异常摘要，不输出账号密码、Cookie、Webhook 或数据库敏感信息。

## 启动方式

推荐通过项目根目录运行：

```powershell
.\.venv\Scripts\python.exe run_job.py "jobs_login\taobao_shop_cookie.py" --log-mode both
```

也可以直接运行：

```powershell
.\.venv\Scripts\python.exe "jobs_login\taobao_shop_cookie.py"
```

独立浏览器自动化调试脚本只用于排查登录页面、滑块、短信或二维码问题，不是批量刷新入口：

```powershell
.\.venv\Scripts\python.exe "API_login\API_TaoXi_login\auto_login\taobao_login_auto.py" --shop-name "示例店铺"
```

需要人工介入时，使用 jobs 入口读取 `config/local.json` 的账号密码，按 `jobs_login/taobao_manual_shop_cookie.py` 内的 `TASK_CONFIG.shops` 选择店铺，自动填写后手动过滑块/短信/扫码，成功后保存页面 Cookie 到 `get_cookie`：

```powershell
.\.venv\Scripts\python.exe run_job.py "jobs_login\taobao_manual_shop_cookie.py" --log-mode both
```

临时只处理一个店铺时再加 `--shop-name`。

如果只想保存本地 Cookie 文件、不写数据库：

```powershell
.\.venv\Scripts\python.exe run_job.py "jobs_login\taobao_manual_shop_cookie.py" --log-mode both --shop-name "示例店铺" --no-db --save-local
```

## 依赖安装

依赖统一安装到项目根 `.venv`，不要在本目录再建虚拟环境。

```powershell
.\.venv\Scripts\python.exe -m pip install -r "API_login\API_TaoXi_login\requirements.txt"
```

`iv8` 是纯协议令牌生成的核心依赖（`requirements.txt` 已含 `iv8>=0.1.3`，需 Python 3.10）。用法与补环境技巧见本目录 `iv8_补环境教程.md`。

## 数据库存储

成功登录后写入 `get_cookie`，读取优先走项目统一 Cookie 查询入口。

写入字段按项目 `DBManager.upsert_cookie(...)` 约定：

- `site`
- `shop_name`
- `cookie_str`
- `cookie`
- `cookie_dict`
- `account`
- `yingdao_account`
- `maintainer_email`

其中 `cookie` 字段按 `get_cookie` 既有浏览器 Cookie JSON 结构保存，便于后续 Playwright/Chrome 场景复用。

## 目录说明

```text
API_login/API_TaoXi_login/
  taobao_login.py              # 主入口/调度：协议登录、Cookie 验证、IV 求解调度、写库、浏览器兜底
  sms_helper.py                # 短信/邮箱读码（协议 IV 与浏览器兜底共用）
  requirements.txt             # 本模块额外依赖
  README.md / PRD.md / SKILL_SUMMARY.md / iv8_补环境教程.md   # 文档与逆向资料

  protocol_login/              # 【协议登录】纯协议、无浏览器
    iv8_token_provider.py      #   iv8 生成 umidToken + bx-ua（主令牌来源）
    iv_sms_solver.py           #   IV 二次身份验证（短信模式）纯协议求解
    js/                        #   iv8 运行时依赖：awsc_baxia.js / um.js / collina.js（必须随仓库提交）

  auto_login/                  # 【自动化登录】DrissionPage 无人值守浏览器兜底
    taobao_login_auto.py       #   独立浏览器自动化调试脚本 + 浏览器填表助手
    slider_helper.py           #   NC 滑块识别/轨迹/拖动
    extract_security_tokens.py #   DrissionPage AWSC 令牌提取（iv8 失败兜底）

  manual_login/                # 【人工介入登录】可见浏览器，人工过滑块/短信/扫码
    taobao_login_manual.py     #   人工介入登录 API（自动填表后人工过验，复用 auto_login 填表助手）
    taobao_manual_task.py      #   人工介入任务辅助层（合并 TASK_CONFIG 与本地账号密码）

  recycle_bin/                 # 测试过程产生的无用文件（已 gitignore，不提交）
```

## 安全约束

- 不提交 `config/local.json`。
- 不提交本地 Cookie 输出文件。
- 日志不得输出密码、完整 Cookie、Webhook、数据库密码或签名 URL。
- JSON 配置文件不支持 `//` 或 `#` 注释，说明文字只能写到 README/PRD。
- 本目录不维护单独 `.git`、`.venv` 或 IDE 配置。
