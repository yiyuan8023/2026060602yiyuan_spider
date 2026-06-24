# yiyuan_spider 发现与决策

## 需求
- 用户要求使用 `$planning-with-files-zh`，先读取现有项目资料，再补 `task_plan.md`、`findings.md`、`progress.md`。
- 本次是项目规划文件补齐，不执行真实平台请求、浏览器登录、钉钉发送或数据库写入。

## 资料来源
| 文件/命令 | 发现 |
|------|------|
| `README.md` | 项目是多平台电商数据采集工具箱，由 API 封装、jobs 任务、Cookie 管理、downloader、Excel 工具和数据库能力组成 |
| `PRD.md` | 项目新规矩是入口收敛、分层清晰、安全约束、验收可执行，不保留旧入口兼容层 |
| `requirements.txt` | 主要依赖包括 requests、playwright、pandas、PyMySQL、loguru、ddddocr、openpyxl、xlrd、fonttools 等 |
| `API_login/API_TaoXi_login/README.md` | 淘系登录模块负责 Cookie 验证、协议登录、自动化兜底、写入 `get_cookie` |
| `API_login/API_TaoXi_login/PRD.md` | 淘系登录目标是多店铺 Cookie 准备，优先复用数据库 Cookie，失败时单店铺通知并继续 |
| `rg --files` | 项目有 API、API_login、jobs、jobs_login、database、downloader、excel_tool、extra、config、cookie_manager 等主要目录 |
| `git status --short` | 工作区已有多处未提交改动，本次不回退、不整理、不纳入计划文件以外的修改 |

## 研究发现

### 项目定位
- `yiyuan_spider` 是采集源码仓库，不是 Web 后台、调度平台或旧项目兼容容器。
- 调度和部署配置统一交由 `F:\05ai_project\2026030502爬虫部署` 维护。
- 原 `tool/` 杂项工具已迁移到独立项目 `F:\05ai_project\2026060603yiyuan_spider_tool`。

### 分层边界
- `API/`：平台请求、Headers、Cookie、签名、token、分页、导出任务、轮询和平台返回解析。
- `jobs/`：最终业务编排，负责表名、站点、店铺、日期、唯一 key、写库和业务日志。
- `API_login/`：平台登录态验证、刷新、Cookie 转换和写库，不承载业务采集。
- `jobs_login/`：登录 Cookie 准备任务入口，负责多店铺配置、失败通知和汇总。
- `downloader/`：普通 HTTP 下载、导出文件落盘、Excel/CSV/ZIP 下载产物解析辅助。
- `excel_tool/`：本地 Excel/CSV/TXT 读取、DataFrame/dict list 输出、入库和导出。
- `database/`：数据库连接、自动建表、补字段、upsert、delete-then-insert、repository 查询。
- `extra/`：日志、请求日志、命令行参数、店铺日期选择、路径、错误摘要等轻量公共能力。
- `config/`：非敏感默认配置、环境变量读取、本地配置模板。

### 统一入口
- 任务推荐启动方式：`.\.venv\Scripts\python.exe run_job.py "<jobs path>" --log-mode both`。
- 日志入口：`from extra.logger_ import logger`。
- 请求日志入口：`from extra.extra_reqlog import req_log`。
- 数据库入口：`from database import DBManager`。
- 下载入口：`from downloader.core import Downloader`。
- Excel 读取入口：`from excel_tool.reader import read_excel_dataframe, read_excel_to_dict, excel_engine`。
- 日期入口：`from date_utils import get_date, get_time_ago, get_recent_days, get_date_range, get_millisecond_timestamp`。

### 代码规模快照
- 排除 `.venv`、`.git`、`.idea`、`log` 后，当前扫描到 Python 文件约 211 个。
- 顶层分布：`API` 73 个，`jobs` 79 个，`API_login` 12 个，`extra` 13 个，`database` 7 个，`config` 7 个，`cookie_manager` 6 个，`excel_tool` 6 个，`downloader` 4 个，`jobs_login` 2 个。
- `API/` 下覆盖赤兔、钉钉、京东、邮箱、拼多多、淘客、商家工作台、光合、生意参谋、万相台、直播、影刀等平台或能力。
- `jobs/` 下覆盖京东、公众号、其他、影刀、手工处理、拼多多、淘系万相台、光合平台、商家工作台、淘宝联盟、生意参谋、直播、赤兔、财务等任务分类。

### 治理线索
- 未发现 `extra.downloader`、`extra.extra_date`、`extra.excel_reader` 的新增引用。
- `from loguru import logger` 仅在 `extra/logger_.py` 中以 `loguru_logger` 形式集中封装，符合集中日志入口方向。
- 直接 `pd.read_excel` 主要出现在 `excel_tool` 内部、少量财务/淘客/API 脚本和注释中；后续触及相关脚本时应优先改走 `excel_tool.reader`，但不要为了本次规划任务大范围改代码。
- 当前 `git status` 已有多处改动和未跟踪内容，后续提交时必须只选择本任务相关文件，避免混入用户既有工作。

### 安全与验收
- 不得在代码、文档、提交信息、日志中写真实 Cookie、数据库密码、Webhook、授权码、签名下载 URL。
- 涉及数据库写入时，默认先单店铺、单日期或小范围样本验证，且需要明确批准。
- 涉及动态导出、淘宝/生意参谋/光合/赤兔/千牛等认证请求时，先验证登录态，再做最小样本，不输出敏感头和签名 URL。
- 文档类变更验收重点：只描述当前项目、不写敏感信息、模块入口和边界清晰、与 README/PRD/技能规则不冲突。

## 技术决策
| 决策 | 理由 |
|------|------|
| 计划三件套放项目根目录 | 方便上下文恢复，也符合 `planning-with-files-zh` 文件位置要求 |
| 以 PRD 阶段路线作为 `task_plan.md` 主线 | 这是项目已有总纲，避免另造一套路线 |
| 将当前扫描发现写入 `findings.md` | 后续排障和治理可直接复用，不必重新扫基础资料 |
| 将本次操作写入 `progress.md` | 便于 `/clear` 或上下文压缩后恢复工作状态 |

## 遇到的问题
| 问题 | 解决方案 |
|------|---------|
| 用户输入 `progress.m` 与技能标准不一致 | 按标准补 `progress.md`，避免生成非标准计划文件 |
| 一次 Python 全量计数命令超时 | 排除 `.venv`、`.git`、`.idea`、`log` 后重新统计成功 |

## 资源
- 项目根目录：`F:\05ai_project\2026060602yiyuan_spider`
- 工具项目：`F:\05ai_project\2026060603yiyuan_spider_tool`
- 调度部署项目：`F:\05ai_project\2026030502爬虫部署`
- 项目主 README：`README.md`
- 项目总纲 PRD：`PRD.md`
- 淘系登录 README：`API_login/API_TaoXi_login/README.md`
- 淘系登录 PRD：`API_login/API_TaoXi_login/PRD.md`

## 视觉/浏览器发现
- 本次未使用浏览器或视觉检查。

---
*每执行 2 次查看/浏览器/搜索操作后更新此文件。*
*防止多模态或临时上下文信息丢失。*
