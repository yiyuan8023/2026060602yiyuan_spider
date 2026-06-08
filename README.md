# yiyuan_spider 项目说明

## 项目定位

`yiyuan_spider` 是一个面向电商平台和内部数据处理场景的 Python 数据采集工具箱。项目主要用于从多个平台采集店铺、商品、流量、交易、售后、财务等数据，并将结果清洗后写入 MySQL 或导出为 Excel/CSV 文件。

当前项目不是单一 Web 服务，也不是单一爬虫脚本，而是由平台 API 封装、执行脚本、通用工具、Cookie 管理和 Excel 处理共同组成的脚本型数据采集仓库。后续任务调度和部署配置统一交由 `F:\05ai_project\2026030502爬虫部署` 维护。

## 适用场景

- 定期采集电商平台经营数据。
- 手工导入 Excel/CSV 报表到数据库。
- 维护多平台 Cookie 登录态。
- 批量执行平台专项采集脚本。
- 将采集结果按业务表写入 MySQL。
- 为财务、运营、店铺分析等场景提供底层数据。

## 技术栈

- Python 3.x
- Requests / aiohttp
- Playwright
- pandas / numpy / openpyxl / xlrd
- PyMySQL / mysql-connector-python
- loguru
- ddddocr / fonttools / pillow
- pdf2image
- PyQt6

依赖清单见：

- `requirements.txt`

## 目录结构

```text
yiyuan_spider/
├── API/                  # 各平台 API 封装
├── config/               # 项目配置入口，读取部署环境变量
├── cookie_manager/       # Cookie 采集、转换、刷新和浏览器登录维护
├── downloader/           # 请求、下载、文件解析辅助
├── excel_tool/           # Excel/CSV 读取、写入、入库工具
├── extra/                # 通用基础能力：日志、数据库、日期、请求、解析、文件处理
├── 执行脚本/              # 具体业务采集脚本
├── 测试/                  # 测试和 UI 实验文件
├── log/                  # 运行日志目录
└── requirements.txt      # Python 依赖
```

说明：原 `tool/` 杂项工具目录已迁移为独立项目：

```text
F:\05ai_project\2026060603yiyuan_spider_tool
```

## 核心模块说明

### API

`API/` 是平台接口封装层。每个子目录对应一个平台或业务系统。

| 目录 | 说明 |
|---|---|
| `API_ChiTu` | 赤兔相关接口 |
| `API_JingDong` | 京东商智相关接口 |
| `API_Pdd` | 拼多多数据中心相关接口 |
| `API_TaoXi_SYCM` | 生意参谋相关接口 |
| `API_TaoKe` | 淘宝联盟相关接口 |
| `API_TianMaoMySeller` | 淘系商家工作台、直播等相关接口 |
| `API_TaoXi_WanXiangTai` | 万相台相关接口 |
| `API_YingDao` | 影刀相关接口 |

API 层主要负责：

- 组织请求地址、Headers、Cookie、签名参数。
- 请求平台接口。
- 处理平台返回结构。
- 部分平台的字体解密、JS 参数生成、压缩包读取等特殊逻辑。

### 执行脚本

`执行脚本/` 是具体任务入口。脚本按平台或业务分类，例如：

- `京东`
- `拼多多`
- `淘系_生意参谋`
- `淘系_淘宝联盟`
- `淘系_万相台`
- `淘系_直播`
- `淘系_赤兔`
- `财务`
- `手工处理`
- `公众号`
- `影刀`

典型脚本流程：

```text
设置采集目标
-> 读取店铺 Cookie 和采集日期
-> 调用 API 层获取数据
-> 字段映射和数据清洗
-> 生成唯一 key
-> 写入 MySQL
-> 记录日志
```

### config

`config/` 是项目配置入口，只保留源码默认值和环境变量读取逻辑，不保存真实数据库密码、Cookie 或服务器敏感信息。

| 文件 | 说明 |
|---|---|
| `runtime.py` | UA、通知邮箱、日志模式等运行配置 |
| `database.py` | 数据库配置读取和校验 |
| `__init__.py` | 对外统一导出配置项 |

### extra

`extra/` 是项目通用能力层，常用文件包括：

| 文件 | 说明 |
|---|---|
| `logger_.py` | loguru 日志封装 |
| `select_shop_date.py` | 获取采集店铺 Cookie 和采集日期 |
| `extra_date.py` | 日期区间、近期日期、月份周期等日期工具 |
| `extra_parser.py` | 命令行参数解析 |
| `excel_reader.py` | Excel 读取相关辅助 |
| `en_to_cn.py` | 英文字段转中文字段 |

### cookie_manager

`cookie_manager/` 用于维护平台 Cookie。

主要能力：

- 从数据库读取旧 Cookie。
- 使用 Playwright 打开浏览器验证登录态。
- 获取新 Cookie。
- 将 Cookie 更新回数据库。
- 提供 Cookie 字符串解析、随机 UA 等辅助方法。

### excel_tool

`excel_tool/` 用于处理本地文件和数据库之间的数据流。

主要能力：

- 读取 `.xlsx`、`.xls`、`.csv`、`.txt`。
- 支持部分加密 Excel 的读取。
- 将 DataFrame 转为字典列表。
- 将文件数据写入 MySQL。
- 将数据导出为 Excel。

## 配置说明

项目当前配置入口位于 `config/`。真实账号、密码、授权码放在项目内的 `config/local.json`，该文件已加入 `.gitignore`，不会上传 Git。

建议长期维护时使用环境变量或 `.env` 文件承载敏感配置。文档中不记录真实账号、密码、服务器地址等敏感值。

本地私有配置模板见：

```text
config/local.example.json
```

真实配置文件位置：

```text
config/local.json
```

如果没有本地配置文件，代码会继续读取环境变量兜底。推荐配置项示例：

```text
MYSQL_HOST=<数据库地址>
MYSQL_PORT=<数据库端口>
MYSQL_DB=<数据库名>
MYSQL_USER=<数据库用户名>
MYSQL_PASSWORD=<数据库密码>
MYSQL_CONFIG_NAME=<默认数据库配置名，可选>
LOG_MODE=file
YIYUAN_UA=<默认请求 User-Agent，可选>
YIYUAN_EMAIL=<默认通知邮箱，可选>
SMTP_HOST=<SMTP服务器，可选>
SMTP_PORT=<SMTP端口，可选>
SMTP_SENDER=<发件邮箱，可选>
SMTP_PASSWORD=<SMTP授权码>
CHITU_PASSWORD=<赤兔导出校验密码，可选>
CHITU_PASSWORDS_JSON=<按店铺配置赤兔导出校验密码的JSON，可选>
NAVICAT_BACKUP_ROOT=<Navicat备份源目录>
DATABASE_BACKUP_DESTINATION=<数据库备份目标目录，可选>
PYTHONIOENCODING=utf-8
```

多数据库配置可在 `config/local.json` 的 `mysql` 节点中按配置名维护，也可使用带配置名前缀的环境变量，例如 `MYSQL_RINNAI_HOST`、`MYSQL_RINNAI_DB`、`MYSQL_RINNAI_USER`、`MYSQL_RINNAI_PASSWORD`。
京东采集、京东导入、林内导入等历史脚本分别使用 `MYSQL_JINGDONG_*`、`MYSQL_JD_IMPORT_*`、`MYSQL_RINNAI_IMPORT_*` 前缀。
赤兔脚本优先读取 `CHITU_PASSWORDS_JSON` 中与店铺名匹配的密码，其次读取统一的 `CHITU_PASSWORD`。

当前代码中常见配置类型：

- 数据库连接配置。
- 日志输出模式：`LOG_MODE=file` 只写文件日志，`LOG_MODE=console` 只输出控制台，`LOG_MODE=both` 文件和控制台同时输出。
- User-Agent。
- 采集店铺列表。
- 目标表名。
- 采集周期。

调度时间、并发策略和部署环境配置不在本仓库维护，统一放在 `F:\05ai_project\2026030502爬虫部署`。

## 数据流

常规自动采集数据流：

```text
数据库 cookie 表
-> select_shop_date 获取店铺和日期
-> 执行脚本调用 API 封装
-> 平台接口返回原始数据
-> 字段转换、清洗、补充店铺和日期
-> 生成 key
-> DBManager 写入目标表
-> log 记录采集结果
```

手工文件处理数据流：

```text
本地 Excel/CSV 文件
-> excel_tool.FileToItems 读取文件
-> DataFrame 转 dict list
-> DBManager 写入目标表
-> log 记录导入结果
```

Cookie 更新数据流：

```text
数据库旧 Cookie
-> Playwright 打开平台页面
-> 检查登录状态
-> 获取新 Cookie
-> 写回数据库
```

## 运行方式

### 安装依赖

```powershell
pip install -r requirements.txt
playwright install chromium
```

### 执行单个脚本

在项目根目录下执行具体业务脚本：

```powershell
python "执行脚本\拼多多\pdd_数据中心_商品数据_商品明细_商品明细效果.py"
```

## 命令行参数

部分脚本会通过 `extra.extra_parser` 读取命令行参数，用于覆盖默认采集日期和店铺。

具体参数格式需要以 `extra/extra_parser.py` 的实现为准。维护脚本时，应优先确认：

- 是否支持开始日期。
- 是否支持结束日期。
- 是否支持指定店铺。
- 默认采集周期是多少。

## 日志

日志封装位于：

```text
extra/logger_.py
```

默认日志目录：

```text
log/
```

日志特性：

- 按日期轮转。
- 普通日志和错误日志分开。
- 保留周期约一年。
- 支持通过配置关闭文件日志，改为控制台输出。
- 会收集部分 Cookie 失效相关错误。

## 数据库

数据库能力由 `database/` 包提供，脚本统一使用 `from database import DBManager`。

主要功能：

- 执行 SQL。
- 查询 Cookie。
- 自动建表。
- 自动补字段。
- 批量插入。
- 根据主键做新增或更新。
- 部分场景支持先删后插。

维护注意：

- 不要在文档或提交信息中记录真实数据库密码。
- 新脚本入库前应确认表名、主键、字段中文名和唯一 key。
- 批量写入前最好先小范围日期测试。
- 如果平台字段变化，可能触发表结构自动新增字段。

## 维护规范建议

当前仓库包含较多运行产物，后续建议重点治理：

- 将 `__pycache__/`、日志文件、打包产物加入 `.gitignore`。
- 清理历史日志、`build/`、`.exe` 等不应长期纳入版本管理的文件。
- 将敏感配置迁移到环境变量或 `.env`。
- 为常用脚本补充用途、表名、默认店铺、默认周期说明。
- 统一执行脚本模板，减少每个脚本重复写店铺、日期、入库逻辑。
- 调度和部署配置集中维护在 `F:\05ai_project\2026030502爬虫部署`，避免在采集源码仓库里继续写死路径。

## 常见风险

- Cookie 过期导致采集失败。
- 平台接口、签名或风控策略变更。
- 中文路径和文件编码在不同终端或 Git 输出中出现乱码。
- 数据库账号密码泄露。
- 运行产物进入 Git，导致仓库噪声很大。
- 单个脚本逻辑分散，新增或排错需要逐文件确认。
- 部分脚本直接写死店铺、表名、日期周期。

## 后续维护入口

排查脚本运行问题时，建议按以下顺序：

1. 确认具体执行脚本。
2. 查看脚本中的 `table_name`、`site`、`shop_name_list` 和默认周期。
3. 查看 `select_shop_date` 返回的店铺和日期。
4. 查看对应 `API/` 模块的请求逻辑。
5. 查看 `log/` 中当天普通日志和错误日志。
6. 确认数据库目标表是否写入成功。

新增采集任务时，建议按以下顺序：

1. 找到同平台相似脚本复制逻辑。
2. 在对应 `API/` 包中补接口封装。
3. 在 `执行脚本/` 对应分类下新增任务脚本。
4. 设置表名、站点、店铺、采集周期。
5. 生成稳定唯一 key。
6. 小日期范围测试入库。
7. 将任务接入 `F:\05ai_project\2026030502爬虫部署` 的调度配置。
