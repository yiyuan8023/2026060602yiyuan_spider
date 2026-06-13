# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-12 23:40:00
- 最近修改：2026-06-13 00:00:00
- 文件用途：自动执行拼多多订单列表页批量导出，按店铺级并发下载区间 CSV、清洗记录并写入既有订单明细表。
- 业务范围：适用于林内拼多多店铺订单查询 -> 订单明细导出自动化，默认按整段日期区间一次导出并复用数据库 cookie 视图。
- 依赖入口：调用 API.API_Pdd.API_Pdd_OrderListExport.PddOrderListExportApi，使用 parser_order_export 规范化记录，使用 select_shop_date 获取店铺和日期，使用 DBManager 入库。
- 验收方式：修改后执行 py_compile；真实采集时先单店铺、单区间验证 Cookie、导出任务、CSV 解析和订单号主键入库。
- 注意事项：正式运行建议通过 run_job.py 启动；日志不得输出完整 Cookie、签名下载 URL 或导出文件原文。
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from API.API_Pdd.API_Pdd_OrderListExport import PddOrderListExportApi
from API.API_Pdd.parser_order_export import normalize_order_export_records
from database import DBManager
from date_utils import get_min_max_timestamps
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date


TABLE_NAME = "rinnai_pdd_订单查询_订单明细_202411"  # noqa
SITE = "拼多多"
PRIMARY_KEY = "订单号"
POLL_SECONDS = 10
TIMEOUT_SECONDS = 600
MAX_WORKERS = 3

SHOP_CONFIGS = [
    {
        "shop_names": ["林内官方旗舰店", "林内八八专卖店"],
        "db_config": None,
        "recent_days": 10,
    },
]


def fetch_shop_report(
    shop_cookie,
    shop_config_by_name,
    start_timestamp: int,
    end_timestamp: int,
):
    """单店铺导出整个时间区间的订单明细，供店铺级并发调用。"""
    shop_name = shop_cookie[0]
    cookie = shop_cookie[1] or shop_cookie[2]
    db_config = shop_config_by_name.get(shop_name, {}).get("db_config")
    api = PddOrderListExportApi(cookie, shop_name=shop_name)
    export_mode = api.resolve_export_mode(start_timestamp, end_timestamp)
    logger.info(
        f"正在采集 {shop_name} 拼多多订单明细，"
        f"mode={export_mode}，time_range={start_timestamp}-{end_timestamp}"
    )
    payload = {
        "groupStartTime": start_timestamp,
        "groupEndTime": end_timestamp,
        "pageNumber": 1,
        "pageSize": 100,
        "rememberTemplate": True,
    }
    raw_items = api.export_order_records(
        payload,
        export_mode=export_mode,
        timeout_seconds=TIMEOUT_SECONDS,
        poll_seconds=POLL_SECONDS,
    )
    items = normalize_order_export_records(raw_items, shop_name=shop_name)
    return {"shop_name": shop_name, "db_config": db_config, "items": items}


def write_shop_items(shop_result):
    """主线程写入单店铺结果，避免在线程间共享数据库连接。"""
    shop_name = shop_result["shop_name"]
    items = shop_result["items"]
    if not items:
        logger.warning(f"{shop_name} 拼多多订单明细无可入库数据")
        return

    with DBManager(db_config=shop_result["db_config"]) as db_manager:
        db_manager.update_insert_data(items, TABLE_NAME, primary_key=PRIMARY_KEY)
    logger.info(f"{shop_name} 拼多多订单明细已入库 {len(items)} 条")
    logger.info("-" * 100)


if __name__ == "__main__":
    logger.info(f"\n{'*' * 120}")

    shop_name_list = []
    for shop_config in SHOP_CONFIGS:
        shop_name_list.extend(shop_config["shop_names"])
    shop_config_by_name = {
        shop_name: shop_config
        for shop_config in SHOP_CONFIGS
        for shop_name in shop_config["shop_names"]
    }
    recent_days = max(shop_config["recent_days"] for shop_config in SHOP_CONFIGS)
    selected_shop_names = shop_name_list or None
    shop_cookies, crawl_day_list = select_shop_date(
        TABLE_NAME,
        SITE,
        selected_shop_names,
        recent_days,
    )
    start_timestamp_ms, end_timestamp_ms = get_min_max_timestamps(crawl_day_list)
    start_timestamp = start_timestamp_ms // 1000
    end_timestamp = (end_timestamp_ms // 1000) - 1

    if not shop_cookies:
        logger.warning("拼多多订单明细没有可执行店铺")
    else:
        worker_count = min(MAX_WORKERS, len(shop_cookies))
        logger.info(
            f"拼多多订单明细店铺级并发开始，店铺数={len(shop_cookies)}，"
            f"并发数={worker_count}，time_range={start_timestamp}-{end_timestamp}"
        )
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_by_shop = {
                executor.submit(
                    fetch_shop_report,
                    shop_cookie,
                    shop_config_by_name,
                    start_timestamp,
                    end_timestamp,
                ): shop_cookie[0]
                for shop_cookie in shop_cookies
            }
            for future in as_completed(future_by_shop):
                shop_name = future_by_shop[future]
                try:
                    write_shop_items(future.result())
                except Exception:
                    logger.exception(f"{shop_name} 拼多多订单明细并发采集失败")
                    raise

    logger.info("*" * 100)
