from API.API_TaoXi_SYCM import Flow  # noqa
from extra.select_shop_date import select_shop_date
from database import DBManager
from extra.logger_ import logger

SHOP_CONFIGS = [
    {"shop_name": "林内官方旗舰店", "db_config": None, "recent_days": 1},
    {"shop_name": "林内厨电旗舰店", "db_config": None, "recent_days": 1},
]


def build_items(raw_items, item_id, item_shop_name, stat_day):
    """补充新版商品来源流量维度，并生成唯一 key。"""
    result = []
    for item in raw_items:
        first_source = item.get("一级来源")
        second_source = item.get("二级来源")
        third_source = item.get("三级来源")
        item.update(
            {
                "商品id": item_id,
                "店铺名称": item_shop_name,
                "统计日期": stat_day,
                "日期类型": "day",
            }
        )
        item["key"] = (
            f"{item['商品id']}_{item['店铺名称']}_{stat_day}_{item['日期类型']}_"
            f"{first_source}_{second_source}_{third_source}"
        )
        result.append(item)
    return result


if __name__ == "__main__":
    shop_name_list = [shop_config["shop_name"] for shop_config in SHOP_CONFIGS]
    shop_config_by_name = {shop_config["shop_name"]: shop_config for shop_config in SHOP_CONFIGS}
    recent_days = max(shop_config["recent_days"] for shop_config in SHOP_CONFIGS)
    table_name = "tb_sycm_流量_商品来源_商品来源流量_新版_202504"  # noqa
    site = "淘系_生意参谋"
    shop_cookies, crawl_day_list = select_shop_date(table_name, site, shop_name_list, recent_days)

    shop_item_ids = {
        "林内官方旗舰店": ["684257114535", "710970001756", "772238538685"],
        "林内厨电旗舰店": ["673717490518"],
    }

    for shop_cookie in shop_cookies:
        cookie = shop_cookie[1]
        shop_name = shop_cookie[0]
        db_config = shop_config_by_name.get(shop_name, {}).get("db_config")
        FlowObj = Flow(cookie)
        for day in crawl_day_list:
            item_ids = shop_item_ids.get(shop_name, [])
            if not item_ids:
                logger.warning(f"{shop_name} 未配置商品ID，跳过")
                continue
            for item_id in item_ids:
                logger.info(f"正在采集{shop_name},{day},{item_id}的数据")
                items1, items2 = FlowObj.goods_from__listen_good_flow_day_new(
                    item_id, day
                )

                items = build_items((items1 or []) + (items2 or []), item_id, shop_name, day)
                if not items:
                    logger.warning(f"{shop_name},{day},{item_id} 新版商品来源流量数据为空，跳过入库")
                    continue

                with DBManager(db_config=db_config) as db_manager:
                    db_manager.update_insert_data(items, table_name, primary_key="key")

            logger.info(f"{shop_name},{day}的数据已入库")
            logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")

# python tb_sycm_流量_商品来源_商品来源流量_新版_202504.py --start-date=2025-03-27 --end-date=2025-04-18 # noqa
