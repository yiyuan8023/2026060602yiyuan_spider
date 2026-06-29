# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一贯
- 创建时间：2026-06-29 19:09:16
- 最近修改：2026-06-29 19:27:21
- 文件用途：执行 DChain_TB 订单-发货管理-订单管理-菜鸟仓采集，补充商家名称并按下单时间和商家名称先删后插入库。
- 业务范围：适用于站点 DChain_TB、店铺/商家名称“杭州碧橙数字技术股份有限公司”、目标页 fulfillment_order_manage_config 的菜鸟仓订单导出。
- 依赖入口：API.API_TaoXi_DC.TaoXiDCOrderExportApi、database.DBManager、date_utils.get_datetime_min_max、extra.select_shop_date。
- 验收方式：执行 py_compile；用单店铺 Cookie 做页面 Token、用户信息和订单列表小样本验证；真实写库前确认日期范围和目标表。
- 注意事项：不在日志输出 Cookie、签名下载 URL、数据库密码或订单敏感明细；delete_insert_data 会按条件删除旧数据后再写入。
"""

import os

from API.API_TaoXi_DC import TaoXiDCOrderExportApi
from database import DBManager
from database.utils import quote_identifier
from date_utils import get_datetime_min_max
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date


def fetch_shop_report(shop_cookie, shop_config_by_name, task_config, start_time, end_time):
    """Create and download one shop's DChain_TB fulfillment-order export."""
    shop_name = shop_cookie[0]
    cookie = shop_cookie[1]
    shop_config = shop_config_by_name.get(shop_name, {})
    api = TaoXiDCOrderExportApi(cookie, page_referer=task_config["page_referer"])

    if task_config["use_latest_success_export"]:
        raw_items = api.download_latest_success_order_export()
    else:
        payload = TaoXiDCOrderExportApi.build_order_export_payload(
            start_time=start_time,
            end_time=end_time,
            warehouse=task_config["warehouse"],
            date_field=task_config["date_field"],
        )
        raw_items = api.export_order_records(payload)

    merchant_name_field = task_config["merchant_name_field"]
    for item in raw_items:
        item[merchant_name_field] = shop_name

    return {
        "shop_name": shop_name,
        "db_config": shop_config.get("db_config"),
        "items": raw_items,
        "start_time": start_time,
        "end_time": end_time,
    }


def write_shop_items(shop_result, task_config):
    """Delete the selected merchant/date range, then insert downloaded rows."""
    shop_name = shop_result["shop_name"]
    raw_items = shop_result["items"]
    if not raw_items:
        logger.warning(f"{shop_name} DChain_TB订单发货管理订单管理菜鸟仓没有数据，跳过入库")
        return

    delete_sql = (
        f"DELETE FROM {quote_identifier(task_config['table_name'])} "
        f"WHERE {quote_identifier(task_config['delete_time_field'])} >= %s "
        f"AND {quote_identifier(task_config['delete_time_field'])} <= %s "
        f"AND {quote_identifier(task_config['merchant_name_field'])} = %s"
    )
    delete_params = (
        shop_result["start_time"],
        shop_result["end_time"],
        shop_name,
    )
    with DBManager(db_config=shop_result["db_config"]) as db_manager:
        db_manager.delete_insert_data(raw_items, task_config["table_name"], delete_sql, delete_params)
    logger.info("-" * 100)


if __name__ == "__main__":
    TASK_CONFIG = {
        "table_name": "tb_DChain_TB_订单_发货管理_订单管理_菜鸟仓_202606",
        "site": "DChain_TB",
        "page_referer": "https://web.scm.tmall.com/pages/3c/fulfillment_order_manage_config",
        "date_field": "tradeCreateTimeRange",
        "delete_time_field": "下单时间",
        "merchant_name_field": "商家名称",
        "warehouse": "all",
        "recent_days": 3,
        "use_latest_success_export": os.environ.get("USE_LATEST_SUCCESS_EXPORT") == "1",
        "shops": [
            {
                "shop_name": "杭州碧橙数字技术股份有限公司",
                "db_config": None,
            },
        ],
    }

    shop_configs = TASK_CONFIG["shops"]
    shop_name_list = [shop_config["shop_name"] for shop_config in shop_configs]
    shop_config_by_name = {shop_config["shop_name"]: shop_config for shop_config in shop_configs}
    shop_cookies, crawl_day_list = select_shop_date(
        TASK_CONFIG["table_name"],
        TASK_CONFIG["site"],
        shop_name_list,
        TASK_CONFIG["recent_days"],
    )
    if not shop_cookies:
        all_shop_cookies, _ = select_shop_date(
            TASK_CONFIG["table_name"],
            TASK_CONFIG["site"],
            [],
            TASK_CONFIG["recent_days"],
        )
        expected_names = set(shop_name_list)
        shop_cookies = [shop_cookie for shop_cookie in all_shop_cookies if shop_cookie[0] in expected_names]

    start_time, end_time = get_datetime_min_max(crawl_day_list)
    logger.info(f"DChain_TB订单发货管理订单管理菜鸟仓时间范围：{start_time} - {end_time}")

    if not shop_cookies:
        logger.warning("DChain_TB订单发货管理订单管理菜鸟仓没有可执行店铺")
    else:
        logger.info(f"DChain_TB订单发货管理订单管理菜鸟仓开始，店铺数={len(shop_cookies)}，店铺顺序执行")
        for shop_cookie in shop_cookies:
            shop_name = shop_cookie[0]
            try:
                shop_result = fetch_shop_report(
                    shop_cookie,
                    shop_config_by_name,
                    TASK_CONFIG,
                    start_time,
                    end_time,
                )
                write_shop_items(shop_result, TASK_CONFIG)
            except Exception:
                logger.exception(f"{shop_name} DChain_TB订单发货管理订单管理菜鸟仓失败")
                raise
    logger.info("*" * 100)
