# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-06 13:28:51
- 最近修改：2026-06-10 21:40:00
- 文件用途：采集拼多多数据中心售后数据，按店铺和统计日期生成入库记录。
- 业务范围：适用于拼多多数据中心-服务数据-售后数据，当前脚本位于未启用目录，目标表和店铺范围以 TASK_CONFIG 为准。
- 依赖入口：调用 API.API_Pdd.PddServiceApi 获取原始数据，使用 build_after_sales_items 解析入库数据，使用 select_shop_date 获取店铺和日期，使用 DBManager 入库。
- 验收方式：修改后执行 py_compile；真实采集时先单店铺、单日期验证 Cookie、字段解析、raw_json_data 和唯一 key。
- 注意事项：售后字段中多个平台类目均值已拆成不同中文字段；正式运行前确认目标表字段扩展符合预期。
"""

from API.API_Pdd import PddServiceApi
from API.API_Pdd.parser_data_center import build_after_sales_items
from database import DBManager
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date


TASK_CONFIG = {
    "table_name": "pdd_数据中心_服务数据_售后数据",
    "source_site": "拼多多",
    "shops": [
        {"shop_names": ["林内官方旗舰店"], "db_config": None, "recent_days": 3},
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

        for shop_cookie in shop_cookies:
            shop_name = shop_cookie[0]
            cookie = shop_cookie[1]
            api = PddServiceApi(cookie, shop_name=shop_name)

            for stat_day in crawl_day_list:
                logger.info(f"正在采集【{shop_name}】{stat_day} 拼多多服务售后数据")
                response_json = api.after_sales_data(stat_day)
                items = build_after_sales_items(response_json, shop_name, stat_day)
                if not items:
                    logger.warning(f"{shop_name},{stat_day} 拼多多服务售后数据无可入库数据")
                    continue

                with DBManager(db_config=db_config) as db_manager:
                    db_manager.update_insert_data(items, table_name, primary_key="key")

                logger.info(f"{shop_name},{stat_day} 拼多多服务售后数据已入库 {len(items)} 条")
                logger.info(f"\n{'-' * 100}")

    logger.info(f"\n{'*' * 120}")
