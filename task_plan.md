# yiyuan_spider 项目任务计划

## 目标
让 `F:\05ai_project\2026060602yiyuan_spider` 后续新增、迁移、排障和验收都有可恢复的计划入口，优先推进入口收敛、边界治理、任务模板统一、数据口径治理和运行观测增强。

## 当前阶段
阶段 1：入口收敛与旧入口治理

## 各阶段

### 阶段 0：项目资料盘点
- [x] 读取根目录 `README.md`
- [x] 读取根目录 `PRD.md`
- [x] 读取 `requirements.txt`
- [x] 读取淘系登录模块 `API_login/API_TaoXi_login/README.md`
- [x] 读取淘系登录模块 `API_login/API_TaoXi_login/PRD.md`
- [x] 扫描项目主要 Python 文件和目录分布
- [x] 将发现记录到 `findings.md`
- **状态：** complete

### 阶段 1：入口收敛与旧入口治理
- [ ] 清理或阻止新增 `extra.downloader`、`extra.extra_date`、`extra.excel_reader` 等旧入口
- [ ] 统一下载入口为 `from downloader.core import Downloader`
- [ ] 统一日志入口为 `from extra.logger_ import logger`
- [ ] 统一数据库入口为 `from database import DBManager`
- [ ] 统一日期能力使用 `date_utils.py`
- [ ] 统一 Excel/CSV 读取优先走 `excel_tool.reader`
- [ ] 对触及文件执行 `py_compile`
- [ ] 必要时执行公共入口导入探针
- **状态：** in_progress

### 阶段 2：平台 API 边界治理
- [ ] 按平台梳理 `API/` 子包职责
- [ ] 将平台请求、签名、分页、导出任务创建和轮询留在 API 层
- [ ] 将表名、店铺、日期、唯一 key、写库留在 jobs 层
- [ ] 将下载和导出文件解析优先收回 `downloader/` 或 `excel_tool/`
- [ ] 保留原始平台返回证据，优先使用 `raw_json_data` 承载不稳定结构
- **状态：** pending

### 阶段 3：任务脚本模板统一
- [ ] 总结标准任务脚本结构
- [ ] 固定任务元信息位置：table/site/shop/date/key/write strategy
- [ ] 统一 `select_shop_date(...)` 用法
- [ ] 统一任务开始、结束、行数、失败摘要日志
- [ ] 优先治理高频 jobs 脚本
- **状态：** pending

### 阶段 4：数据口径治理
- [ ] 梳理核心业务表清单
- [ ] 记录数据来源、统计粒度、主键、更新频率
- [ ] 标记高风险字段和平台易变字段
- [ ] 为核心表建立最小数据校验
- **状态：** pending

### 阶段 5：运行观测增强
- [ ] 标准化成功、失败、耗时、行数日志
- [ ] 区分 Cookie 失效、接口失败、数据为空、入库失败
- [ ] 汇总任务结果
- [ ] 必要时接入邮件、钉钉或其它通知
- **状态：** pending

## 关键问题
1. 优先治理哪些高频任务脚本，需要按实际调度使用频率确认。
2. 哪些脚本允许小范围真实请求或数据库写入，需要用户明确批准。
3. 哪些核心表属于下游强依赖，需要先补口径说明再动脚本。

## 已做决策
| 决策 | 理由 |
|------|------|
| 计划文件放在项目根目录 | `planning-with-files-zh` 要求计划三件套放项目目录，不放技能目录 |
| 使用 `progress.md` 而不是 `progress.m` | 技能标准文件名是 `progress.md`，用户输入疑似漏写扩展名 |
| 不处理当前工作区已有改动 | `git status` 显示多处既有变更，与本次补计划文件无关，不能误改或回退 |
| 后续任务默认通过 `run_job.py` 启动 | README/PRD 均指定它负责项目根路径、`sys.path`、工作目录和 `LOG_MODE` |
| 敏感信息只允许在本地私有配置中存在 | README/PRD 明确禁止账号、密码、Cookie、Webhook、数据库密码进入文档、日志和提交 |

## 遇到的错误
| 错误 | 尝试次数 | 解决方案 |
|------|---------|---------|
| Python 文件全量计数命令超时 | 1 | 改为排除 `.venv`、`.git`、`.idea`、`log` 后重新统计 |

## 备注
- 做重大决策前重新读取 `task_plan.md`、`findings.md`、`progress.md`。
- 每完成一个阶段后更新阶段状态。
- 遇到错误必须记录，避免重复踩坑。
- 外部平台请求、浏览器登录、钉钉发送、数据库写入默认不做，除非用户明确批准。
