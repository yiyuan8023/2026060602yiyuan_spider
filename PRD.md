# Yiyuan Spider PRD

## Positioning

当前仓库是业务采集项目，负责平台业务数据采集、下载、解析、标准化和入库。

登录 Cookie 准备能力已经迁移到独立项目：

```text
F:\05ai_project\2026060601yiyuan_spider_login
```

当前仓库不再保留 `API_login/` 和 `jobs_login/`。

## Scope

- `API/`: 平台业务 API、导出任务、分页、解析和下载入口。
- `jobs/`: 业务采集脚本，负责店铺、日期、表名、业务字段和数据库写入编排。
- `database/`: 数据库连接、表结构、Cookie 查询面和写入基础设施。
- `downloader/`: 文件下载、响应校验、Excel/CSV/ZIP 解析。
- `excel_tool/`: Excel/CSV 读取和入库工具。
- `extra/`: 日志、请求记录、命令行解析、文件路径等通用能力。

## Login Boundary

- 登录刷新、短信验证码、钉钉失败通知、Cookie 巡检在独立登录项目执行。
- 当前采集项目只消费可用 Cookie。
- 不在普通 `jobs/` 脚本里实现登录、验证码、浏览器兜底或 Cookie 写回流程。
- 新增登录适配默认进入独立登录项目，除非另有明确评审结论。

## Acceptance

- 业务采集脚本不依赖 `API_login/` 或 `jobs_login/`。
- 删除登录目录后，当前项目保留业务采集能力。
- 敏感配置只在本机私有配置或环境变量中维护，不进入 Git。
