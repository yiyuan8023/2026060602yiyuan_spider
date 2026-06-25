# -*- coding: utf-8 -*-
"""Collect DChain merchant-warehouse order-list tags from the page API."""

from concurrent.futures import ThreadPoolExecutor, as_completed

from API.API_TaoXi_DC import TaoXiDCOrderListApi
from database import DBManager
from database.utils import quote_identifier
from date_utils import get_date_min_max
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date


TABLE_NAME = "tb_DChain_订单管理行业_商家仓_页面订单标识_202606"
SITE = "DChain"
MAX_WORKERS = 1
WAREHOUSE = "merchant"
DATE_FIELD = "sysCreateTimeRange"
DELETE_TIME_FIELD = "系统创建时间"
PAGE_SIZE = 100

SHOP_CONFIGS = [
    {
        "shop_name": "安徽碧橙网络技术有限公司",
        "db_config": None,
        # "db_config": "bc",
        "recent_days": 3,
    },
    # {
    #     "shop_name": "四川碧橙新零售有限公司",
    #     "db_config": "bc",
    #     "recent_days": 60,
    # },
]


def build_time_range(crawl_day_list):
    """Convert selected crawl days to DChain system-create time range."""
    start_date, end_date = get_date_min_max(crawl_day_list)
    return f"{start_date} 00:00:00", f"{end_date} 23:59:59"


def fetch_shop_records(shop_cookie, shop_config_by_name, start_time, end_time):
    """Fetch one shop's visible order tags from DChain order-list API."""
    shop_name = shop_cookie[0]
    cookie = shop_cookie[1]
    shop_config = shop_config_by_name.get(shop_name, {})
    api = TaoXiDCOrderListApi(cookie)
    payload = TaoXiDCOrderListApi.build_order_list_payload(
        start_time=start_time,
        end_time=end_time,
        warehouse=WAREHOUSE,
        date_field=DATE_FIELD,
    )
    items = api.fetch_order_records(payload, page_size=PAGE_SIZE)
    for item in items:
        item["商家名称"] = shop_name
    return {
        "shop_name": shop_name,
        "db_config": shop_config.get("db_config"),
        "items": items,
        "start_time": start_time,
        "end_time": end_time,
    }


def write_shop_items(shop_result):
    """Delete selected system-create range, then insert current page-list rows."""
    shop_name = shop_result["shop_name"]
    items = shop_result["items"]
    if not items:
        logger.warning(f"{shop_name} DChain商家仓页面订单标识没有数据，跳过入库")
        return

    delete_sql = (
        f"DELETE FROM {quote_identifier(TABLE_NAME)} "
        f"WHERE {quote_identifier(DELETE_TIME_FIELD)} >= %s "
        f"AND {quote_identifier(DELETE_TIME_FIELD)} <= %s "
        f"AND {quote_identifier('商家名称')} = %s"
    )
    delete_params = (
        shop_result["start_time"],
        shop_result["end_time"],
        shop_name,
    )
    with DBManager(db_config=shop_result["db_config"]) as db_manager:
        db_manager.delete_insert_data(items, TABLE_NAME, delete_sql, delete_params)
    logger.info("-" * 100)


if __name__ == "__main__":
    shop_name_list = [shop_config["shop_name"] for shop_config in SHOP_CONFIGS]
    shop_config_by_name = {shop_config["shop_name"]: shop_config for shop_config in SHOP_CONFIGS}
    recent_days = max(shop_config["recent_days"] for shop_config in SHOP_CONFIGS)
    shop_cookies, crawl_day_list = select_shop_date(
        TABLE_NAME,
        SITE,
        shop_name_list,
        recent_days,
    )
    if not shop_cookies:
        all_shop_cookies, _ = select_shop_date(TABLE_NAME, SITE, [], recent_days)
        expected_names = set(shop_name_list)
        shop_cookies = [shop_cookie for shop_cookie in all_shop_cookies if shop_cookie[0] in expected_names]

    start_time, end_time = build_time_range(crawl_day_list)
    logger.info(f"DChain商家仓页面订单标识时间范围：{start_time} - {end_time}")

    if not shop_cookies:
        logger.warning("DChain商家仓页面订单标识没有可执行店铺")
    else:
        worker_count = min(MAX_WORKERS, len(shop_cookies))
        logger.info(f"DChain商家仓页面订单标识开始，店铺数={len(shop_cookies)}，并发数={worker_count}")
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_by_shop = {
                executor.submit(
                    fetch_shop_records,
                    shop_cookie,
                    shop_config_by_name,
                    start_time,
                    end_time,
                ): shop_cookie[0]
                for shop_cookie in shop_cookies
            }
            for future in as_completed(future_by_shop):
                shop_name = future_by_shop[future]
                try:
                    write_shop_items(future.result())
                except Exception:
                    logger.exception(f"{shop_name} DChain商家仓页面订单标识失败")
                    raise
    logger.info("*" * 100)
