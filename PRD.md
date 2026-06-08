# yiyuan_spider 新项目作战准则 PRD

## 1. 文档定位

| 项目 | 内容 |
|---|---|
| 文档名称 | `2026060602yiyuan_spider` 新项目作战准则 PRD |
| 文档类型 | 项目总纲、模块边界、迭代路线、验收标准 |
| 适用项目 | `F:\05ai_project\2026060602yiyuan_spider` |
| 主要受众 | 项目维护者、Codex 执行代理 |
| 核心目标 | 让后续新增、迁移、排障、验收都有明确入口和边界 |

本 PRD 不再只是“项目说明”。它是 `2026060602yiyuan_spider` 的新项目作战准则。

凡是后续新增平台、迁移历史脚本、抽公共能力、修复采集问题，都先按本文判断模块归属、调用入口、验收动作和禁区。

## 2. 项目定位

`yiyuan_spider` 是一个面向电商平台和内部数据处理场景的 Python 数据采集项目。

项目主要承担：

- 多平台经营数据采集。
- 平台导出文件下载与解析。
- Excel/CSV 手工文件读取与入库。
- 店铺 Cookie 登录态读取、更新和失效排查。
- 数据清洗、字段转换、唯一 key 生成。
- MySQL 自动建表、补字段、批量写入。
- 运行日志、请求日志和错误定位。

本项目不是 Web 后台，不是调度平台，也不是旧项目兼容容器。它是新的采集源码仓库。后续规则按新项目标准执行，不保留旧入口，不为了历史路径继续新增兼容层。

## 3. 总体原则

### 3.1 新项目原则

- 只维护 `F:\05ai_project\2026060602yiyuan_spider` 当前项目。
- 历史代码迁移进来后，必须服从当前模块边界。
- 不再新增 `extra.downloader`、`extra.extra_date`、`extra.excel_reader` 这类旧入口。
- 不为了少改几行代码保留同义包装。
- 能直接调用现有公共入口，就直接调用。
- 真缺公共能力时，扩展对应公共模块，而不是在业务脚本里临时堆一份。

### 3.2 分层原则

项目按职责分层：

```text
jobs 任务脚本层
  -> 平台 API 层
  -> 通用能力层
  -> 数据库层
  -> 日志与观测层
```

每一层只做自己的活。跨层乱拿、复制公共逻辑、把平台细节写进任务脚本，后续都视为需要治理的问题。

### 3.3 安全原则

- 不在代码、文档、提交信息里写真实 Cookie、数据库密码、授权码、签名下载 URL。
- `config/local.json` 只留本地，不进 Git。
- 日志可记录平台名、店铺名、任务 ID、表名、日期、行数、错误摘要。
- 日志不得记录完整 Cookie、Authorization、数据库密码、敏感请求参数、带签名的文件下载地址。
- 排查平台导出时，默认只做小范围样本，不写真实数据库，除非明确批准。

## 4. 项目目录边界

### 4.1 `API/`

职责：

- 平台请求封装。
- Headers、Cookie、签名、token、分页、导出任务创建、状态轮询。
- 平台返回结构解析。
- 平台特殊逻辑，例如 mtop 签名、字体解密、压缩包字段读取。
- 将标准化后的结果交给任务脚本或 downloader/parser。

禁止：

- 不在 API 层写最终业务表名、店铺列表、采集日期循环。
- 不在 API 层直接配置日志 sink。
- 不在 API 层绕开 downloader 自己写一次性下载器。
- 不在 API 层写数据库 cookie 拼接 SQL。

### 4.2 `jobs/`

职责：

- 最终业务编排入口。
- 定义平台、站点、店铺列表、表名、采集周期。
- 调用 `select_shop_date(...)` 获取店铺和日期。
- 调用对应 `API/` 模块。
- 补充店铺名、统计日期、业务字段。
- 生成稳定唯一 key。
- 调用数据库写入。
- 输出任务开始、结束、行数、失败原因日志。

禁止：

- 不复制 API 层请求逻辑。
- 不复制 downloader、date_utils、excel_tool.reader 已有能力。
- 不在脚本里拼接 cookie 查询 SQL。
- 不把平台无关的通用解析沉淀在单个业务脚本里。

统一启动：

- 根目录 `run_job.py` 是任务脚本推荐启动入口。
- `run_job.py` 负责设置项目根目录、`sys.path`、工作目录和 `LOG_MODE`，再执行目标任务脚本。
- 调度器优先调用 `run_job.py "jobs\...\xxx.py"`，不要依赖调度器当前工作目录。
- 单个任务脚本仍应保持业务编排职责，不应各自堆重复启动补丁。

### 4.3 `downloader/`

统一入口：

```python
from downloader.core import Downloader
```

职责：

- 普通 HTTP 下载。
- 导出文件落盘。
- Excel、CSV、ZIP 等下载产物解析。
- 文件编码识别和平台导出文件通用处理。

硬规范：

- 下载必须优先走 `downloader`。
- 平台导出文件解析能放 downloader 的，放 downloader。
- downloader 不能满足时，先扩展 downloader，再改业务脚本。
- 不再使用 `extra.downloader`。

### 4.4 `extra/`

职责：

- 跨模块通用辅助能力。
- 日志入口。
- 请求日志入口。
- 命令行参数解析。
- 店铺日期选择。
- 路径、文件、字段转换、错误摘要等轻量工具。

硬规范：

```python
from extra.logger_ import logger
from extra.extra_reqlog import req_log
```

禁止：

- 不直接在业务模块导入 `loguru.logger`。
- 不在业务模块调用 `logger.add(...)`、`logger.remove(...)`。
- 不新增 `extra.extra_date.py`。
- 不新增 `extra.excel_reader.py`。

### 4.5 `database/`

统一入口：

```python
from database import DBManager
```

职责：

- 数据库连接。
- SQL 执行。
- 事务和上下文管理。
- 自动建表。
- 自动补字段。
- 批量 upsert。
- 删除后插入等写入策略。
- Cookie 等业务查询通过 repository 管理。

模块边界：

- `database/manager.py`：连接、执行 SQL、事务、关闭。
- `database/schema.py`：建表、字段推断、补字段、触发器。
- `database/writer.py`：批量写入、upsert、delete-then-insert。
- `database/repositories/`：业务查询，例如 cookie 查询。

硬规范：

- 任务脚本不拼 `IN (...)` cookie SQL。
- 店铺名列表交给 repository 参数化处理。
- 不把 `0`、`0.0`、`False` 错转成 `None`。
- id、订单号、商品编码、key 等按字符串类字段保守处理。
- 批量大小保持保守并可配置。

### 4.6 `date_utils.py`

统一入口：

```python
from date_utils import get_date, get_time_ago, get_recent_days, get_date_range, get_millisecond_timestamp
```

职责：

- 日期格式转换。
- 最近 N 天。
- 日期区间。
- 月份周期。
- 13 位毫秒时间戳。

硬规范：

- 日期必须优先走 `date_utils.py`。
- 只改日期输出格式时，直接调用 `get_date(value, "...")`。
- mtop `t` 参数或 13 位时间戳使用 `get_millisecond_timestamp()`。
- 不再新增 `extra.extra_date.py`。
- 不在业务脚本里复制日期区间逻辑。

### 4.7 `excel_tool/`

统一入口：

```python
from excel_tool.reader import read_excel_dataframe, read_excel_to_dict, excel_engine
```

职责：

- Excel/CSV/TXT 读取。
- DataFrame 输出。
- dict list 输出。
- Excel engine 识别。
- 平台导出文件常见 warning 的集中处理。
- 文件入库和导出工具。

硬规范：

- API 层和任务脚本读取 Excel 时，优先走 `excel_tool.reader`。
- 不直接在业务脚本里新增 `pandas.read_excel(...)`。
- 不全局屏蔽 `openpyxl` 或 `UserWarning`。
- `Workbook contains no default style` 这类 warning 可以保留原始输出，再由 reader 给短日志说明。
- 不再新增 `extra/excel_reader.py` 或 `extra/extra_excel.py`。

### 4.8 `config/`

职责：

- 非敏感默认配置。
- 环境变量读取。
- 本地配置模板。
- UA、数据库、邮箱、京东、赤兔等配置入口。

硬规范：

- `config/local.example.json` 可以提交。
- `config/local.json` 不提交。
- 真实数据库密码、Cookie、SMTP 授权码不进文档、不进 Git。
- 新增配置先考虑环境变量和本地配置文件，不写死到业务脚本。

### 4.9 `cookie_manager/`

职责：

- 浏览器登录态维护。
- Cookie 读取、刷新、转换、保存。
- 平台登录状态验证。

边界：

- Cookie 采集和刷新在这里。
- 任务脚本只读取可用 Cookie，不承载浏览器登录流程。
- 真实 Cookie 不写入日志、文档或提交信息。

## 5. 标准业务流程

### 5.1 自动采集流程

```text
任务脚本定义 table/site/shop/date
-> select_shop_date(...) 读取店铺 Cookie 和采集日期
-> API 模块请求平台数据
-> downloader 处理下载和导出文件
-> 字段转换、补充公共字段、生成 key
-> DBManager 写入 MySQL
-> logger 记录任务结果
```

验收重点：

- 能定位脚本入口。
- 能定位 API 模块。
- 能定位目标表。
- 能定位 Cookie 来源。
- 能定位日期生成规则。
- 能定位下载文件处理入口。
- 能定位入库逻辑。

### 5.2 手工 Excel/CSV 导入流程

```text
准备本地文件
-> excel_tool.reader 读取 DataFrame 或 dict list
-> 清洗字段
-> 生成业务 key
-> DBManager 写入目标表
-> logger 记录文件名、行数、表名、结果
```

验收重点：

- 文件不存在时明确报错。
- reader 能返回预期结构。
- 字段名清晰稳定。
- 写入前有目标表和唯一 key。

### 5.3 平台导出文件流程

```text
API 创建导出任务
-> API 轮询任务状态
-> 获得下载地址
-> downloader 下载文件
-> downloader 或 excel_tool.reader 解析文件
-> 任务脚本补业务字段并入库
```

验收重点：

- API 层负责创建和轮询。
- downloader 负责下载和文件解析辅助。
- 任务脚本负责表名、店铺、日期、key、入库。
- 不记录完整签名下载 URL。

### 5.4 Cookie 更新流程

```text
读取旧 Cookie
-> Playwright 打开平台页面
-> 判断登录状态
-> 获取新 Cookie
-> 写回数据库 cookie 表
-> logger 记录平台、店铺、成功或失败原因
```

验收重点：

- 登录有效时能返回新 Cookie。
- 登录失败时有明确原因。
- 风控或人工验证不强行绕过。
- 不在日志里打印完整 Cookie。

## 6. 新增或迁移脚本准则

### 6.1 新增脚本必须明确

- 平台名称。
- 业务页面或接口。
- 脚本路径。
- API 模块路径。
- 目标表名。
- 默认站点。
- 默认店铺列表。
- 默认采集周期。
- 唯一 key 组成。
- 是否写库。
- 是否下载文件。
- 是否读取 Excel/CSV。
- 是否需要 Cookie。

### 6.2 迁移历史脚本必须处理

- 旧下载逻辑迁移到 `downloader`。
- 旧日志逻辑迁移到 `extra.logger_`。
- 旧数据库入口迁移到 `database`。
- 旧日期逻辑迁移到 `date_utils.py`。
- 旧 Excel 读取迁移到 `excel_tool.reader`。
- 删除或停止引用旧入口。
- 保留必要业务注释，删除无效历史注释。

### 6.3 注释标准

允许写中文注释，但要写业务知识，不写废话。

适合注释：

- 请求职责。
- 签名生成。
- token 刷新。
- 导出任务创建和轮询。
- 店铺列表来源。
- 表名含义。
- 采集周期。
- 唯一 key 规则。
- 入库策略。

不适合注释：

- Python 基础语法解释。
- 过期路径。
- 真实 Cookie、密码、签名 URL。
- 和当前代码不一致的历史说明。

## 7. 验收标准

### 7.1 文档类变更

文档变更验收：

- 文档只描述当前项目 `2026060602yiyuan_spider`。
- 文档不写真实敏感配置。
- 模块入口和边界清晰。
- 与 README、skill 规则不冲突。
- 中文内容在 PowerShell 和编辑器中不应出现保存层面的乱码。

### 7.2 代码迁移类变更

每次迁移或重构后至少执行：

```powershell
$env:PYTHONUTF8 = "1"
.\.venv\Scripts\python.exe -m py_compile <变更的 Python 文件>
```

必要时增加导入探针：

```powershell
$env:PYTHONUTF8 = "1"
@'
from downloader.core import Downloader
from extra.logger_ import logger
from database import DBManager
from excel_tool.reader import read_excel_dataframe, read_excel_to_dict, excel_engine
from date_utils import get_date, get_recent_days, get_date_range, get_millisecond_timestamp
print("import probe ok")
'@ | .\.venv\Scripts\python.exe -
```

迁移验收还要确认：

- 没有新增旧入口引用。
- 没有直接导入 `loguru.logger`。
- 没有在任务脚本里直接拼 cookie SQL。
- 没有在业务脚本里新增重复下载器。
- 没有在业务脚本里复制日期区间工具。
- 没有直接新增 `pandas.read_excel(...)` 绕过 reader。

### 7.3 数据写入类变更

涉及数据库写入时，默认先小范围验证：

- 单店铺。
- 单日期或小日期范围。
- 样本行数可控。
- 明确目标表。
- 明确唯一 key。
- 明确写入策略是 upsert 还是 delete-then-insert。
- 失败时日志能定位表名、日期、店铺、错误摘要。

没有明确批准时，不做大范围真实数据库写入。

### 7.4 平台导出分析类变更

涉及 Taobao、Shengyican、Guanghe、mtop 等动态导出时：

- 优先用项目 cookie 获取流程。
- 先 HTTP 验证登录态。
- 必要时再用 Playwright 抓取网络请求。
- 过滤无关埋点请求。
- 只验证一个样本日期。
- 验证文件名、sheet、列数、行数、业务 key。
- 不输出真实 Cookie、签名 URL、授权信息。

### 7.5 Skill 变更

如果本次变更包含 Codex skill 创建或更新，必须同步维护：

```text
C:\Users\admin\.codex\skills\<skill-name>\SKILL.md
C:\Users\admin\.codex\skills\<skill-name>\README.zh-CN.md
```

并执行校验：

```powershell
$env:PYTHONUTF8 = "1"
py -3 "C:\Users\admin\.codex\skills\.system\skill-creator\scripts\quick_validate.py" "C:\Users\admin\.codex\skills\<skill-name>"
```

中文说明文档至少包含：

- 用途。
- 触发场景。
- 文件位置。
- 使用方式。
- 维护注意事项。
- 验证方式。

## 8. 后续迭代路线

### 阶段一：入口收敛

目标：

- 清掉旧入口。
- 统一下载、日志、数据库、日期、Excel 读取。
- 让新脚本有明确模板。

重点动作：

- 清理 `extra.extra_date.py` 引用。
- 清理 `extra.excel_reader.py` 引用。
- 清理 `extra.downloader` 引用。
- 统一 `from extra.logger_ import logger`。
- 统一 `from database import DBManager`。
- 统一 `excel_tool.reader`。

验收：

- 旧入口没有新增引用。
- 迁移文件通过 `py_compile`。
- 公共入口导入探针通过。

### 阶段二：平台 API 边界治理

目标：

- API 层只管平台请求。
- 任务脚本只管业务编排。
- downloader 处理下载和文件产物。

重点动作：

- 按平台梳理 API 模块职责。
- 把下载逻辑从 API 或任务脚本抽回 downloader。
- 把平台通用导出流程沉淀到对应 API 基类或服务类。
- 保留平台差异，避免过度抽象。

验收：

- 新增同平台接口时能复用现有 API 结构。
- 任务脚本不出现大段平台请求细节。
- 导出文件下载和解析路径清楚。

### 阶段三：任务脚本模板统一

目标：

- 新增采集任务更快。
- 排查问题更直接。
- 表名、店铺、日期、key、入库规则更稳定。

重点动作：

- 总结标准任务脚本结构。
- 统一任务元信息位置。
- 统一 `select_shop_date(...)` 使用方式。
- 统一日志开始、结束、行数、失败摘要。
- 高优先级迁移高频脚本。

验收：

- 新脚本能按模板快速落地。
- 排查时能在固定位置找到 table/site/shop/date/key。
- 常见失败日志格式一致。

### 阶段四：数据口径治理

目标：

- 降低下游用数风险。
- 让核心表字段、主键、粒度有说明。

重点动作：

- 梳理核心业务表清单。
- 记录数据来源、主键、统计粒度、更新频率。
- 标记高风险字段。
- 为核心表建立最小数据校验。

验收：

- 核心表有口径说明。
- key 规则可追踪。
- 字段变化能被记录。

### 阶段五：运行观测增强

目标：

- 更快发现失败任务。
- 更快定位失败原因。

重点动作：

- 标准化任务开始、结束、耗时、行数日志。
- 区分 Cookie 失效、接口失败、数据为空、入库失败。
- 汇总任务结果。
- 需要时接入邮件、钉钉或其他通知。

验收：

- 每次任务能看出成功与否。
- 失败能定位到平台、店铺、日期、表名和原因。
- Cookie 失效能明确到平台和店铺。

## 9. 维护检查清单

新增或迁移脚本前，先确认：

- 平台和业务页面是否明确。
- 目标表名是否明确。
- 默认站点是否明确。
- 默认店铺是否明确。
- 默认采集周期是否明确。
- Cookie 来源是否明确。
- 唯一 key 是否明确。
- 是否需要下载文件。
- 是否需要读取 Excel/CSV。
- 是否写库，写入策略是什么。

改完后，至少确认：

- `py_compile` 通过。
- 必要导入探针通过。
- 没有旧入口新增引用。
- 没有敏感信息进入代码、文档或日志。
- 小范围样本能跑通，或者明确说明未跑原因。

排查失败任务时，按顺序查：

1. 任务脚本路径。
2. table/site/shop/date/key。
3. `select_shop_date(...)` 返回。
4. 对应 API 请求逻辑。
5. downloader 下载和解析结果。
6. `excel_tool.reader` 读取结果。
7. `database` 写入日志。
8. `log/` 当天普通日志和错误日志。

## 10. 禁区

- 不新增旧入口兼容文件。
- 不提交真实敏感配置。
- 不在业务脚本里硬写数据库密码。
- 不在业务脚本里复制公共下载器。
- 不在业务脚本里复制日期工具。
- 不在业务脚本里绕开 `excel_tool.reader` 直接新增 Excel 读取逻辑。
- 不直接配置 loguru sink。
- 不未经批准大范围写真实数据库。
- 不把调度平台职责塞回采集源码仓库。

## 11. 结论

`2026060602yiyuan_spider` 后续按新项目治理。

短期重点不是大重写，而是把入口收拢、边界立稳、验收跑起来。旧脚本可以迁移，但迁移后必须服从新规矩。下载走 downloader，日志走 `logger_`，数据库走 `database`，日期走 `date_utils.py`，Excel 走 `excel_tool.reader`。

这套规矩立住以后，再做平台 API 治理、脚本模板统一、数据口径治理和运行观测增强。先把刀磨正，再去砍硬活。
