# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-26 12:20:00
- 最近修改：2026-06-26 12:20:00
- 文件用途：读取企微文档《新零售台账》中的“客户跟进”在线表，解析后按来源文件ID和来源Sheet全量刷新入库。
- 业务范围：适用于企微文档站点下“企微文档-一元”Cookie 对应账号可访问的客户跟进 smartsheet。
- 依赖入口：调用 API.API_WeCom_Docs.WeComDocsFileApi 读取企微文档 opendoc 数据，使用 parser_new_retail_customer_follow 解析字段，使用 DBManager 全删全入，日志走 extra.logger_。
- 验收方式：修改后执行 py_compile；通过只读探针验证文件名、文件ID、Sheet 名称、字段数量和解析行数。
- 注意事项：不得输出真实 Cookie、手机号、客户地址或数据库敏感配置；新脚本默认 db_config=None，由项目默认测试库承接，正式库只能人工改。
"""

from typing import List

from API.API_WeCom_Docs import (
    WeComDocsFileApi,
    parse_new_retail_customer_follow_records,
    validate_new_retail_customer_follow_headers,
)
from database import DBManager
from database.utils import quote_identifier
from extra.logger_ import logger


TASK_CONFIG = {
    # "table_name": "qw_企微文档_新零售台账_客户跟进_202606",
    "table_name": "rinnai_四川_直营台账_创新新零售_客户来源_2025",
    "site": "企微文档",
    "document_url": "https://doc.weixin.qq.com/smartsheet/s3_AXsA2Ab7APwCNJptxqk0vTNCc1VcR?scode=AEsApAfUAB8eRPpeRxAeAAfwb5AOA&tab=q979lj&viewId=vukaF8",
    "file_id": "s3_AXsA2Ab7APwCNJptxqk0vTNCc1VcR",
    "file_name": "新零售台账",
    "sheet_name": "客户跟进",
    "table_id": "q979lj",
    "view_id": "vukaF8",
    "shops": [
        {
            "shop_name": "企微文档-一元",
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
    """校验客户跟进表头，并补充来源站点、文件、URL 和 Sheet 信息。"""
    validate_new_retail_customer_follow_headers(raw_items)
    return parse_new_retail_customer_follow_records(
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
    expected_file_name = TASK_CONFIG["file_name"]
    sheet_name = TASK_CONFIG["sheet_name"]
    table_id = TASK_CONFIG["table_id"]
    view_id = TASK_CONFIG["view_id"]

    for shop_config in TASK_CONFIG["shops"]:
        shop_name = shop_config["shop_name"]
        db_config = shop_config["db_config"]

        with DBManager(db_config) as db_manager:
            shop_cookie = db_manager.select_cookie(site, shop_name)

        if not shop_cookie or not shop_cookie[1]:
            raise RuntimeError(f"未找到可用 Cookie：站点={site}，店铺={shop_name}")

        cookie = shop_cookie[1]
        api = WeComDocsFileApi(cookie, referer=document_url)
        file_info = api.resolve_document_info(document_url)

        actual_file_id = str(file_info.get("local_pad_id") or "")
        actual_file_name = str(file_info.get("title") or "")
        actual_table_id = str(file_info.get("table_id") or "")
        actual_view_id = str(file_info.get("view_id") or "")
        if actual_file_id != expected_file_id:
            raise RuntimeError(f"企微文档文件ID不匹配: expected={expected_file_id}, actual={actual_file_id}")
        if actual_file_name != expected_file_name:
            raise RuntimeError(f"企微文档文件名不匹配: expected={expected_file_name}, actual={actual_file_name}")
        if actual_table_id != table_id:
            raise RuntimeError(f"企微文档 Sheet ID 不匹配: expected={table_id}, actual={actual_table_id}")
        if actual_view_id != view_id:
            raise RuntimeError(f"企微文档视图ID不匹配: expected={view_id}, actual={actual_view_id}")

        logger.info(
            f"正在采集【{shop_name}】企微文档新零售台账客户跟进，"
            f"title={file_info.get('title')}，pad_id={file_info.get('pad_id')}，table_id={table_id}"
        )

        raw_items = api.read_smartsheet_records(file_info, sheet_name=sheet_name)
        if not raw_items:
            logger.warning(f"{shop_name} 企微文档新零售台账客户跟进为空，跳过入库")
            continue

        items = build_items(raw_items, site, document_url, file_info, sheet_name)
        if not items:
            logger.warning(f"{shop_name} 企微文档新零售台账客户跟进没有有效数据，跳过入库")
            continue

        delete_sql = (
            f"DELETE FROM {quote_identifier(table_name)} "
            f"WHERE {quote_identifier('来源文件ID')}=%s AND {quote_identifier('来源Sheet')}=%s"
        )
        delete_params = (expected_file_id, sheet_name)
        with DBManager(db_config) as db_manager:
            db_manager.delete_insert_data(items, table_name, delete_sql, delete_params)

        logger.info(f"{shop_name} 企微文档新零售台账客户跟进已全量刷新入库，rows={len(items)}")
        logger.info(f"\n{'-' * 100}")

    logger.info(f"\n{'*' * 120}")
