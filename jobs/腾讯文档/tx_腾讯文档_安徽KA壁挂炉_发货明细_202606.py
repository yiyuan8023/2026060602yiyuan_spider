# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-26 09:52:00
- 最近修改：2026-06-26 09:52:00
- 文件用途：导出腾讯文档中的安徽KA壁挂炉发货明细，过滤无订单日期行并补充来源信息后按文件ID和Sheet刷新写入目标表。
- 业务范围：适用于腾讯文档站点下“腾讯文档-一元”Cookie 对应账号可访问的《安徽KA壁挂炉发货对接》在线表格，入库 Sheet 为“发货明细”。
- 依赖入口：调用 API.API_Tencent_Docs.TencentDocsFileApi 导出腾讯文档 Excel，使用 parser_anhui_ka_delivery 解析字段，使用 DBManager 全删全入，日志走 extra.logger_。
- 验收方式：修改后执行 py_compile；涉及接口或入库逻辑时通过 run_job.py 验证文件信息、解析行数、目标表行数和日期范围。
- 注意事项：不得输出真实 Cookie、签名下载 URL、手机号、收货地址或数据库敏感配置；新 job 默认使用测试库，正式库配置只能由人工手动修改。
"""

from typing import List

from API.API_Tencent_Docs import (
    TencentDocsFileApi,
    parse_anhui_ka_delivery_records,
    validate_anhui_ka_delivery_headers,
)
from database import DBManager
from database.utils import quote_identifier
from extra.logger_ import logger


TASK_CONFIG = {
    # "table_name": "tx_腾讯文档_安徽KA壁挂炉_发货明细_202606",
    "table_name": "rinnai_分销ka对公_安徽壁挂炉",
    "site": "腾讯文档",
    "document_url": "https://docs.qq.com/sheet/DV2h4Z012bndnZGdt?tab=BB08J2",
    "file_id": "300000000$WhxgMvnwgdgm",
    "sheet_name": "发货明细",
    "shops": [
        {
            "shop_name": "腾讯文档-一元",
            "db_config": "rinnai",
        },
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
    validate_anhui_ka_delivery_headers(raw_items)
    return parse_anhui_ka_delivery_records(
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

        with DBManager(db_config) as db_manager:
            shop_cookie = db_manager.select_cookie(site, shop_name)

        if not shop_cookie or not shop_cookie[1]:
            raise RuntimeError(f"未找到可用 Cookie：站点={site}，店铺={shop_name}")

        cookie = shop_cookie[1]
        api = TencentDocsFileApi(cookie, referer=document_url)
        file_info = api.resolve_document_info(document_url)
        actual_file_id = str(file_info.get("local_pad_id") or "")
        if actual_file_id != expected_file_id:
            raise RuntimeError(f"腾讯文档文件ID不匹配: expected={expected_file_id}, actual={actual_file_id}")
        logger.info(
            f"正在采集【{shop_name}】腾讯文档安徽KA壁挂炉发货明细，"
            f"title={file_info.get('title')}，"
            f"domain_id={file_info.get('domain_id')}，"
            f"pad_id={file_info.get('pad_id')}"
        )

        raw_items = api.download_excel_records(file_info, sheet_name=sheet_name)
        if not raw_items:
            logger.warning(f"{shop_name} 腾讯文档安徽KA壁挂炉发货明细为空，跳过入库")
            continue

        items = build_items(raw_items, site, document_url, file_info, sheet_name)
        if not items:
            logger.warning(f"{shop_name} 腾讯文档安徽KA壁挂炉发货明细没有有效数据，跳过入库")
            continue

        delete_sql = (
            f"DELETE FROM {quote_identifier(table_name)} "
            f"WHERE {quote_identifier('来源文件ID')}=%s AND {quote_identifier('来源Sheet')}=%s"
        )
        delete_params = (expected_file_id, sheet_name)
        with DBManager(db_config) as db_manager:
            db_manager.delete_insert_data(items, table_name, delete_sql, delete_params)

        logger.info(f"{shop_name} 腾讯文档安徽KA壁挂炉发货明细已全量刷新入库，rows={len(items)}")
        logger.info(f"\n{'-' * 100}")

    logger.info(f"\n{'*' * 120}")
