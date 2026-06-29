# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-25 17:53:24
- 最近修改：2026-06-25 17:53:24
- 文件用途：下载 WPS 文档中的阙里代发表格，过滤无订单日期行并补充来源信息后按文件ID和Sheet刷新写入目标表。
- 业务范围：适用于 WPS 文档站点下“wps文档-一元”店铺的阙里代发明细，来源文档为脚本配置的 KDocs 链接。
- 依赖入口：调用 API.API_WPS_Docs.WpsDocsFileApi 下载 KDocs Excel，使用 parser_queli_daifa 解析字段，使用 DBManager 全删全入，日志走 extra.logger_。
- 验收方式：修改后执行 py_compile；涉及接口或入库逻辑时通过 run_job.py 验证文件信息、解析行数、目标表行数和日期范围。
- 注意事项：不得输出真实 Cookie、签名下载 URL、手机号、收货地址或数据库敏感配置；当前策略是按来源文件ID和来源Sheet删除后入库。
"""

from typing import List

from API.API_WPS_Docs import (
    WpsDocsFileApi,
    parse_queli_daifa_records,
    validate_queli_daifa_headers,
)
from database import DBManager
from database.utils import quote_identifier
from extra.logger_ import logger


# 最终任务脚本只保留店铺、表名、文档来源和入库编排；接口下载逻辑放在 API 层。
TASK_CONFIG = {
    # "table_name": "tb_wps文档_阙里代发_代发明细_202606",
    "table_name": "rinnai_分销bu_阙里代发_202603",
    "site": "wps文档",
    "document_url": "https://www.kdocs.cn/l/cupnKvq9TZLe",
    "file_id": "496257908410",
    "sheet_name": "阙里代发",
    "shops": [
        {"shop_name": "wps文档-一元", "db_config": "rinnai"},
    ],
}


def build_items(
        raw_items: List[dict],
        source_site: str,
        source_url: str,
        source_file_info: dict,
        source_sheet_name: str,
) -> List[dict]:
    """过滤无订单日期行，并补充来源站点、文件、URL 和 Sheet 信息。"""
    validate_queli_daifa_headers(raw_items)
    return parse_queli_daifa_records(
        raw_items,
        source_site=source_site,
        source_url=source_url,
        file_info=source_file_info,
        sheet_name=source_sheet_name,
    )


if __name__ == "__main__":
    table_name = TASK_CONFIG["table_name"]
    site = TASK_CONFIG["site"]
    document_url = TASK_CONFIG["document_url"]
    expected_file_id = TASK_CONFIG["file_id"]
    sheet_name = TASK_CONFIG["sheet_name"]

    for shop_config in TASK_CONFIG["shops"]:
        shop_name = shop_config["shop_name"]
        db_config = shop_config["db_config"]

        # WPS 文档 Cookie 来自项目 cookie 视图；Cookie 字符串使用 shop_cookie[1]。
        with DBManager(db_config) as db_manager:
            shop_cookie = db_manager.select_cookie(site, shop_name)

        if not shop_cookie or not shop_cookie[1]:
            raise RuntimeError(f"未找到可用 Cookie：站点={site}，店铺={shop_name}")

        cookie = shop_cookie[1]
        api = WpsDocsFileApi(cookie, referer=document_url)
        file_id = api.resolve_file_id(document_url)
        if str(file_id) != expected_file_id:
            raise RuntimeError(f"WPS文档文件ID不匹配: expected={expected_file_id}, actual={file_id}")
        file_info = api.get_file_info(file_id)
        file_info["id"] = str(file_id)
        logger.info(
            f"正在采集【{shop_name}】WPS文档阙里代发明细，"
            f"file_id={file_info.get('id')}，"
            f"name={file_info.get('name')}，"
            f"version={file_info.get('version')}，"
            f"size={file_info.get('size')}"
        )

        raw_items = api.download_excel_records(file_id, sheet_name=sheet_name)
        if not raw_items:
            logger.warning(f"{shop_name} WPS文档阙里代发明细为空，跳过入库")
            continue

        # 统一在执行层补业务维度和来源信息，API 层只返回文档原始明细。
        items = build_items(raw_items, site, document_url, file_info, sheet_name)
        if not items:
            logger.warning(f"{shop_name} WPS文档阙里代发明细没有有效数据，跳过入库")
            continue

        delete_sql = (
            f"DELETE FROM {quote_identifier(table_name)} "
            f"WHERE {quote_identifier('来源文件ID')}=%s AND {quote_identifier('来源Sheet')}=%s"
        )
        delete_params = (expected_file_id, sheet_name)
        with DBManager(db_config) as db_manager:
            db_manager.delete_insert_data(items, table_name, delete_sql, delete_params)

        logger.info(f"{shop_name} WPS文档阙里代发明细已全量刷新入库，rows={len(items)}")
        logger.info(f"\n{'-' * 100}")

    logger.info(f"\n{'*' * 120}")
