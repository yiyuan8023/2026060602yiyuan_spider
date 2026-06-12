# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-06 13:28:51
- 最近修改：2026-06-10 21:40:00
- 文件用途：采集拼多多数据中心商品明细效果数据，按店铺和统计日期生成入库记录。
- 业务范围：适用于拼多多数据中心-商品数据-商品明细-商品明细效果，目标表和店铺范围以 TASK_CONFIG 为准。
- 依赖入口：调用 API.API_Pdd.PddGoodsApi 获取原始数据，使用 build_goods_detail_items 解析入库数据，使用 select_shop_date 获取店铺和日期，使用 DBManager 入库。
- 验收方式：修改后执行 py_compile；真实采集时先单店铺、单日期验证 Cookie、分页、字段解析、raw_json_data 和唯一 key。
- 注意事项：正式运行建议通过 run_job.py 设置项目根路径和 LOG_MODE；不得输出真实 Cookie、签名参数或数据库敏感配置。
"""

from API.API_Pdd import PddGoodsApi
from API.API_Pdd.parser_data_center import build_goods_detail_items
from database import DBManager
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date


TASK_CONFIG = {
    "table_name": "pdd_数据中心_商品数据_商品明细_商品明细效果_202606",
    "source_site": "拼多多",
    "page_size": 50,
    "max_pages": 20,
    "shops": [
        {
            "shop_names": ["林内官方旗舰店", "林内八八专卖店", "林内辰之光专卖店"],
            "db_config": "rinnai_py",  # noqa
            "recent_days": 3,
        },
    ],
}


if __name__ == "__main__":
    table_name = TASK_CONFIG["table_name"]
    source_site = TASK_CONFIG["source_site"]
    page_size = TASK_CONFIG["page_size"]
    max_pages = TASK_CONFIG["max_pages"]

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
            api = PddGoodsApi(cookie, shop_name=shop_name)

            for stat_day in crawl_day_list:
                logger.info(f"正在采集【{shop_name}】{stat_day} 拼多多商品明细效果")
                all_items = []
                seen_keys = set()
                page_num = 1

                while page_num <= max_pages:
                    response_json, font_mapping = api.goods_detail(
                        stat_day,
                        stat_day,
                        page_num=page_num,
                        page_size=page_size,
                    )
                    items = build_goods_detail_items(response_json, font_mapping, shop_name, stat_day)
                    if not items:
                        logger.info(f"{shop_name},{stat_day} 第 {page_num} 页无可入库数据，停止分页")
                        break

                    new_items = []
                    duplicate_count = 0
                    for item in items:
                        item_key = item.get("key")
                        if item_key in seen_keys:
                            duplicate_count += 1
                            continue
                        seen_keys.add(item_key)
                        new_items.append(item)

                    all_items.extend(new_items)
                    logger.info(
                        f"{shop_name},{stat_day} 第 {page_num} 页解析 {len(items)} 条，"
                        f"新增 {len(new_items)} 条，重复 {duplicate_count} 条"
                    )
                    if duplicate_count == len(items):
                        logger.warning(f"{shop_name},{stat_day} 第 {page_num} 页全部重复，停止分页")
                        break
                    if len(items) < page_size:
                        break
                    page_num += 1
                else:
                    logger.warning(f"{shop_name},{stat_day} 已达到最大分页数 {max_pages}，停止继续请求")

                if not all_items:
                    logger.warning(f"{shop_name},{stat_day} 拼多多商品明细效果无可入库数据")
                    continue

                with DBManager(db_config=db_config) as db_manager:
                    db_manager.update_insert_data(all_items, table_name, primary_key="key")

                logger.info(f"{shop_name},{stat_day} 拼多多商品明细效果已入库 {len(all_items)} 条")
                logger.info(f"\n{'-' * 100}")

    logger.info(f"\n{'*' * 120}")
