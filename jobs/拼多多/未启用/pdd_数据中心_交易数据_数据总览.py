# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-06 13:28:51
- 最近修改：2026-06-10 21:40:00
- 文件用途：采集拼多多数据中心交易数据总览，按店铺和日期范围生成入库记录。
- 业务范围：适用于拼多多数据中心-交易数据-数据总览，当前脚本位于未启用目录，目标表和店铺范围以 TASK_CONFIG 为准。
- 依赖入口：调用 API.API_Pdd.PddTradeApi 获取原始数据，使用 build_trade_overview_items 解析入库数据，使用 select_shop_date 获取店铺和日期，使用 DBManager 入库。
- 验收方式：修改后执行 py_compile；真实采集时先单店铺、单日期验证 Cookie、字体映射、字段解析、raw_json_data 和唯一 key。
- 注意事项：正式运行建议通过 run_job.py 设置项目根路径和 LOG_MODE；未确认前不要批量扩大店铺和日期范围。
"""

from API.API_Pdd import PddTradeApi
from API.API_Pdd.parser_data_center import build_trade_overview_items
from database import DBManager
from date_utils import get_date_min_max
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date


TASK_CONFIG = {
    "table_name": "pdd_数据中心_交易数据_数据总览",
    "source_site": "拼多多",
    "shops": [
        {"shop_names": ["林内官方旗舰店"], "db_config": None, "recent_days": 30},
    ],
}


if __name__ == "__main__":
    table_name = TASK_CONFIG["table_name"]
    source_site = TASK_CONFIG["source_site"]

    for shop_config in TASK_CONFIG["shops"]:
        db_config = shop_config["db_config"]
        shop_cookies, crawl_day_list = select_shop_date(
            table_name,
            source_site,
            shop_config["shop_names"],
            shop_config["recent_days"],
        )
        start_date, end_date = get_date_min_max(crawl_day_list)

        for shop_cookie in shop_cookies:
            shop_name = shop_cookie[0]
            cookie = shop_cookie[1]
            api = PddTradeApi(cookie, shop_name=shop_name)

            logger.info(f"正在采集【{shop_name}】{start_date} 至 {end_date} 拼多多交易数据总览")
            response_json, font_mapping = api.trade_overview(start_date, end_date)
            items = build_trade_overview_items(response_json, font_mapping, shop_name)
            if not items:
                logger.warning(f"{shop_name},{start_date}-{end_date} 拼多多交易数据总览无可入库数据")
                continue

            with DBManager(db_config=db_config) as db_manager:
                db_manager.update_insert_data(items, table_name, primary_key="key")

            logger.info(f"{shop_name},{start_date}-{end_date} 拼多多交易数据总览已入库 {len(items)} 条")
            logger.info(f"\n{'-' * 100}")

    logger.info(f"\n{'*' * 120}")
