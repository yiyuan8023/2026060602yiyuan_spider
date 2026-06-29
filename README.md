# Yiyuan Spider

业务采集项目。登录 Cookie 准备能力已经迁移到独立项目：

```text
F:\05ai_project\2026060601yiyuan_spider_login
```

当前仓库不再保留 `API_login/` 和 `jobs_login/`。采集任务只消费已经准备好的 Cookie。

## Layout

```text
yiyuan_spider/
├── API/                  # 各平台业务 API 封装
├── config/               # 项目配置入口
├── cookie_manager/       # 通用 Cookie 转换和历史辅助能力
├── database/             # 数据库连接、表结构和写入基础设施
├── downloader/           # 下载、文件校验和 Excel/CSV/ZIP 解析
├── excel_tool/           # Excel/CSV 读取和入库工具
├── extra/                # 日志、请求、解析、文件处理等通用能力
├── jobs/                 # 业务采集脚本
├── run_job.py            # 任务脚本统一启动入口
└── log/                  # 运行日志目录
```

## Run

业务采集任务仍通过 `run_job.py` 启动：

```powershell
.\.venv\Scripts\python.exe run_job.py "jobs\path\to\task.py" --log-mode both
```

登录 Cookie 刷新、Cookie 巡检、钉钉失败通知等入口请到独立登录项目执行。

## Rules

- 不在本仓库新增 `API_login/` 或 `jobs_login/`。
- 普通业务采集脚本只读取 Cookie，不承载登录流程。
- 不在日志、文档和提交记录中输出真实 Cookie、账号密码、Webhook、数据库密码或邮箱授权码。
- 新增平台登录适配优先放到独立登录项目。
