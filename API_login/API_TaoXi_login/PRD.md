# PRD - 淘系登录 Cookie 准备模块

## 1. 背景

生意参谋、淘宝卖家后台等淘系业务脚本依赖有效 Cookie 才能稳定访问平台接口。旧项目 `2026061401taobao_login` 已验证协议登录可用，但原实现以本地文件和单项目配置为主，不符合 `yiyuan_spider` 的 API/任务脚本分层、统一配置、统一数据库 Cookie 管理和统一通知要求。

本需求将旧项目能力迁移到 `yiyuan_spider`：

- 登录 API 放在 `API_login/API_TaoXi_login`。
- 启动脚本放在 `jobs_login`。
- 店铺账号密码放在 `config/local.json`。
- Cookie 结果写入数据库 `get_cookie`。
- Cookie 首次复用从数据库 `cookie` 读取。
- 单店铺失败不阻断其它店铺。
- 失败时支持钉钉通知。

## 2. 目标

构建一个可复用的淘系登录 Cookie 准备能力，为下游采集任务提供稳定的生意参谋/卖家后台 Cookie。

核心目标：

- 支持多店铺批量准备 Cookie。
- 优先复用数据库已有 Cookie，减少登录频率。
- Cookie 失效后自动刷新。
- 保留旧项目协议登录主路径。
- 协议登录失败时保留自动化登录兜底。
- 成功后写入 `get_cookie`，供统一 `cookie` 视图/查询逻辑合并读取。
- 单店铺失败后继续执行下一个店铺。
- 店铺失败时发钉钉告警，通知失败不得影响主流程。

## 3. 非目标

- 不在 `API_login/API_TaoXi_login` 下单独维护 Git 仓库。
- 不在 `API_login/API_TaoXi_login` 下单独维护虚拟环境。
- 不再支持旧配置字段 `account` / `sub_name`。
- 不再使用旧项目 `config.json` 作为正式配置入口。
- 不把账号、密码、Cookie、Webhook、数据库密码写入日志或文档。
- 不在 API 层硬编码最终业务表名、店铺列表和调度策略。

## 4. 使用角色

- 运营采集任务维护者：需要定期刷新淘系 Cookie。
- 平台 API 开发者：需要在其它淘系能力中复用 Cookie。
- 运维/调度人员：需要知道失败店铺、失败原因和是否需要人工介入。

## 5. 模块边界

### 5.1 API 层

路径：`API_login/API_TaoXi_login/taobao_login.py`

职责：

- 验证已有 Cookie。
- 提取 AWSC 安全参数。
- 执行协议登录。
- 执行 `asyncUrls` 补全。
- 协议失败后自动化登录兜底。
- 生成数据库可存储 Cookie 结构。
- 调用 `DBManager.upsert_cookie(...)` 写入 `get_cookie`。

### 5.2 任务层

路径：`jobs_login/taobao_shop_cookie.py`

职责：

- 从 `config/local.json` 读取多店铺配置。
- 调用 `select_shop_date(table_name, site, [shop_name], recent_days)` 获取已有 Cookie。
- 按店铺调用 API 层准备 Cookie。
- 捕获单店铺异常，记录失败并继续下一个店铺。
- 发送单店铺失败钉钉通知。
- 输出成功/失败汇总。

### 5.3 配置层

路径：`config/local.json`

职责：

- 保存本机真实账号密码、钉钉 Webhook、数据库等敏感配置。
- 不提交 Git。
- JSON 文件必须是标准 JSON，不允许 `//` 或 `#` 注释。

## 6. 业务流程

### 6.1 正常流程

1. 任务脚本启动。
2. 读取 `taobao_login` 配置。
3. 遍历店铺列表。
4. 按 `site + shop_name` 从数据库读取已有 Cookie。
5. 验证 Cookie 是否可用。
6. Cookie 可用时返回 `db_cookie_valid`，不重新登录。
7. Cookie 不可用时执行协议登录。
8. 协议登录成功后补全 `asyncUrls`。
9. 保存 Cookie 到 `get_cookie`。
10. 继续处理下一个店铺。
11. 全部店铺处理完成后输出汇总。

### 6.2 降级流程

协议登录失败时：

1. 记录协议登录状态。
2. 进入自动化登录兜底。
3. 自动化登录填写账号密码并处理协议弹窗。
4. 如检测到 NC 滑块，调用 `slider_helper.py` 处理滑块。
5. 如检测到短信验证，调用 `sms_helper.py` 尝试读取验证码。
6. 自动化登录成功则写入 `get_cookie`。
7. 自动化登录失败则返回失败状态。

### 6.3 单店铺失败流程

单店铺出现异常或最终状态不是 `success` / `db_cookie_valid` 时：

1. 记录错误日志。
2. 发送钉钉 Markdown 通知。
3. 通知失败只记录 warning。
4. 将店铺加入失败列表。
5. 继续执行下一个店铺。

### 6.4 人工介入流程

协议登录和自动化过滑块都不稳定时，允许使用人工介入脚本：

1. `jobs_login/taobao_manual_shop_cookie.py` 按脚本内 `TASK_CONFIG.shops` 选择本次处理店铺。
2. 从 `config/local.json` 按店铺名读取账号密码。
3. 调用 `API_login/API_TaoXi_login/taobao_login_manual.py` 打开可见浏览器。
4. API 层自动切换密码登录、填写账号密码并点击登录。
5. 用户在浏览器中手动完成滑块、短信或扫码。
6. API 层检测页面离开登录页后跳转卖家后台补全 Cookie。
7. 读取浏览器页面原始 Cookie 列表。
8. 默认写入 `get_cookie`，`cookie` 字段保存页面 Cookie JSON 结构。
9. 可选通过 `--save-local` 保存本地 Cookie 文件；可通过 `--no-db` 禁止写库。

## 7. 配置需求

### 7.1 淘系登录配置

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

约束：

- `login_id` 必填。
- `password` 在需要重新登录时必填。
- `shop_name` 必须与数据库 Cookie 店铺名一致。
- `site` 当前固定为 `生意参谋`。
- 不兼容 `account` / `sub_name`。
- `source_site` / `target_site` 已合并为 `site`。

### 7.2 钉钉通知配置

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

约束：

- `notify_enabled=true` 才发送通知。
- 机器人启用加签时，必须配置 `robot_secret`。
- 机器人启用关键词安全策略时，必须配置 `notify_keyword`。
- `notify_keyword` 会自动补进标题和正文。

## 8. 数据库需求

### 8.1 读取

任务层通过项目既有方法读取：

```python
shop_cookies, crawl_day_list = select_shop_date(table_name, site, shop_name_list, recent_days)
```

其中 Cookie 常用元组形态：

- `row[0]`: 店铺名
- `row[1]`: 请求头 Cookie 字符串
- `row[2]`: 浏览器 Cookie JSON

### 8.2 写入

API 层写入 `get_cookie`，字段按 `DBManager.upsert_cookie(...)` 约定：

- `site`
- `shop_name`
- `cookie_str`
- `cookie`
- `cookie_dict`
- `account`
- `yingdao_account`
- `maintainer_email`

`cookie` 字段使用浏览器 Cookie JSON 结构，兼容 `get_cookie` 既有存储形式。

## 9. 状态定义

| 状态 | 含义 | 后续动作 |
| --- | --- | --- |
| `db_cookie_valid` | 数据库 Cookie 有效 | 跳过登录 |
| `success` | 重新登录成功 | 写入 `get_cookie` |
| `unknown` | 登录结果未明确成功 | 标记店铺失败，继续下一个 |
| `captcha` | 触发验证码/滑块 | 标记店铺失败或进入自动化兜底 |
| `network_error` | 网络异常 | 按重试策略处理 |
| `error:*` | 登录或解析异常 | 标记店铺失败，通知 |

## 10. 验收标准

### 10.1 静态验收

- `py_compile` 通过：

```powershell
.\.venv\Scripts\python.exe -B -m py_compile API_login\API_TaoXi_login\taobao_login.py jobs_login\taobao_shop_cookie.py
```

- `config/local.json` 是合法 JSON。
- 文档不包含真实账号、密码、Cookie、Webhook、数据库密码。

### 10.2 配置验收

- 多店铺配置能被 `load_task_config()` 正确读取。
- 每个店铺必须有 `shop_name` 和 `login_id`。
- `site` 为 `生意参谋`。
- 不再读取 `account` / `sub_name`。

### 10.3 流程验收

- 已有 Cookie 有效时，不触发重新登录。
- Cookie 失效时，触发协议登录。
- 协议登录成功后写入 `get_cookie`。
- 单店铺失败后继续执行后续店铺。
- 钉钉通知失败不影响主流程。

### 10.4 小范围真实验收

在明确允许真实登录和写库后，只做单店铺验证：

- 验证 Cookie 读取来源。
- 验证登录状态。
- 验证 `get_cookie` 写入结果。
- 验证 `cookie` 读取面能合并读取新 Cookie。
- 验证钉钉失败通知是否命中关键词策略。

## 11. 风险与限制

- 淘宝登录协议可能变化，需要维护 RSA、AWSC、Havana 登录参数和 `asyncUrls` 处理逻辑。
- 安全参数提取依赖浏览器环境，风控升级时可能失败。
- 自动化登录可能触发滑块、短信或人工验证。
- Cookie 有效期不稳定，平台可能提前失效。
- 钉钉机器人关键词、安全签名配置错误会导致通知失败。
- JSON 配置文件不能写注释，说明文字必须写 README/PRD。

## 12. 后续规划

- 将自动化登录兜底的浏览器关闭异常做更细粒度保护。
- 为失败状态增加更明确分类，例如账号密码错误、滑块失败、短信验证、网络异常。
- 增加只验证 Cookie、不触发登录的 dry-run 参数。
- 增加单店铺命令行筛选参数，方便排查某个店铺。
- 梳理旧项目迁移文件，删除确认不再使用的抓包样例和调试截图。
