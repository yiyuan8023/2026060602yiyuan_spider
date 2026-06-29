# 淘系登录 Cookie 准备模块

本目录是 `yiyuan_spider` 项目内的淘系登录 API 模块，覆盖 **生意参谋（SYCM）** 和 **DChain 供应链** 两个站点的自动化登录。模块不单独维护 Git 仓库、不单独维护虚拟环境，统一使用项目根目录的 `.venv`、`config/local.json`、`database` 和 `extra.logger_`。

## 当前定位

- API 层：`API_login/API_TaoXi_login/`（三子包架构，见下方目录说明）
- SYCM 启动脚本：`jobs_login/taobao_shop_cookie.py`
- DChain 启动脚本：`jobs_login/dchain_cookie.py`
- 配置文件：`config/local.json`（`taobao_login` 段 = SYCM，`dchain_login` 段 = DChain）
- 配置示例：`config/local.example.json`
- Cookie 读取面：数据库 `cookie` 视图/表
- Cookie 写入面：数据库 `get_cookie`

## 登录链路

两个站点共用同一套 Havana 登录基础设施（RSA + iv8 AWSC + JSVMP），差异由 `st_callback` 参数区分：

### 共用流程（base_login）

1. 从 `config/local.json` 读取多店铺/账号配置。
2. 每个店铺先通过 `select_shop_date()` 读取数据库已有 Cookie。
3. `prepare_shop_cookie()` 先验证数据库 Cookie 是否仍可用；**有效则滚动刷新覆盖写回 `get_cookie`，不重登、不发短信**。
4. Cookie 失效或不存在时，走纯协议登录。
5. iv8 生成 `umidToken` + `bx-ua`（无浏览器，~4s），iv8 不可用回落 DrissionPage 提取。
6. 若返回 IV 二次验证，`iv_sms_solver` 纯协议求解。
7. 登录成功后通过 `st_callback` 建立目标站点 session → 校验 → 写 `get_cookie`。
8. 纯协议失败时降级到浏览器自动化兜底。
9. 单店铺失败时记录日志 + 钉钉通知，继续下一个。

### SYCM 特有

- `st_callback=None`（默认）：简单 `returnUrl?st=xxx` 即完成 session 建立。
- 验证 URL：`myseller.taobao.com`

### DChain 特有

- `st_callback=_dchain_st_callback`：3 步建立 DChain session（basic_login_proxy → updateSession → autoLogin）。
- 登录入口：`havanalogin.taobao.com/mini_login.htm?appName=ascp&fromSite=31`（iframe 嵌入）。
- 验证 URL：`web.scm.tmall.com`
- 浏览器兜底需进入 `iframe#alibaba-login-box` 才能操作表单和滑块。

## 配置格式

### SYCM（`config/local.json` → `taobao_login` 段）

```json
{
  "taobao_login": {
    "table_name": "get_cookie",
    "site": "生意参谋",
    "recent_days": 1,
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

### DChain（`config/local.json` → `dchain_login` 段）

```json
{
  "dchain_login": {
    "table_name": "get_cookie",
    "site": "DChain",
    "recent_days": 1,
    "defaults": {
      "timeout": 30,
      "max_retries": 3,
      "retry_delay": 5
    },
    "shops": [
      {
        "shop_name": "示例账号",
        "login_id": "bc_xxx",
        "password": "登录密码"
      }
    ]
  }
}
```

说明：

- `shop_name` 是数据库 Cookie 按店铺/账号查询和写入时使用的标识名。
- `login_id` 是登录页使用的完整账号（SYCM: `主账号:子账号`，DChain: `bc_xxx`）。
- `password` 是该登录账号对应的密码。
- SYCM 的 `site` 使用 `生意参谋`，DChain 使用 `DChain`。

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

### SYCM Cookie 准备

```powershell
.\.venv\Scripts\python.exe run_job.py "jobs_login\taobao_shop_cookie.py" --log-mode both
```

### DChain Cookie 准备

```powershell
.\.venv\Scripts\python.exe run_job.py "jobs_login\dchain_cookie.py" --log-mode both
```

### 独立浏览器调试

```powershell
.\.venv\Scripts\python.exe "API_login\API_TaoXi_login\auto_login\taobao_login_auto.py" --shop-name "示例店铺"
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
├── API_TaoXi_base_login/            # 【共用基础】三层共用的核心逻辑
│   ├── havana.py                    #   Havana 协议登录核心（配置/RSA/令牌/login/prepare_shop_cookie）
│   ├── cookie_manager.py            #   Cookie CRUD + DB 读写 + 验证刷新
│   ├── browser_fallback.py          #   浏览器自动化兜底（iframe检测/滑块/短信循环）
│   └── __init__.py                  #   统一 re-export 所有公共符号
│
├── API_TaoXi_SYCM_login/           # 【生意参谋】站点特有常量 + prepare_sycm_cookie()
│   └── __init__.py
│
├── API_TaoXi_DC_login/             # 【DChain】站点特有常量 + 3步ST回调 + prepare_dchain_cookie()
│   └── __init__.py
│
├── protocol_login/                  # 【协议登录】纯协议、无浏览器
│   ├── iv8_token_provider.py        #   iv8 生成 umidToken + bx-ua
│   ├── iv_sms_solver.py             #   IV 二次验证短信模式纯协议求解
│   └── js/                          #   iv8 运行时 JS（awsc_baxia/um/collina）
│
├── auto_login/                      # 【自动化登录】DrissionPage 浏览器兜底
│   ├── taobao_login_auto.py         #   浏览器自动化调试 + 填表助手
│   ├── slider_helper.py             #   NC 滑块识别/轨迹/拖动
│   └── extract_security_tokens.py   #   DrissionPage AWSC 令牌提取
│
├── sms_helper.py                    # 短信/邮箱读码（协议 IV 与浏览器兜底共用）
├── requirements.txt                 # 本模块额外依赖（含 iv8>=0.1.3）
├── README.md                        # 本文件
├── 逆向经验贴.md                     # 合并版逆向文档（Part A: SYCM + Part B: DChain）
├── iv8_补环境教程.md                  # iv8 用法与补环境技巧
└── recycle_bin/                      # 测试过程产生的无用文件（gitignore）
```

## 安全约束

- 不提交 `config/local.json`。
- 不提交本地 Cookie 输出文件。
- 日志不得输出密码、完整 Cookie、Webhook、数据库密码或签名 URL。
- JSON 配置文件不支持 `//` 或 `#` 注释，说明文字只能写到 README/PRD。
- 本目录不维护单独 `.git`、`.venv` 或 IDE 配置。
