from API.API_TaoXi_SYCM import Goods  # noqa
from extra.select_shop_date import select_shop_date
from database import DBManager
from extra.logger_ import logger

SHOP_CONFIGS = [
    {"shop_name": "林内官方旗舰店", "db_config": None, "recent_days": 1},
    {"shop_name": "林内厨电旗舰店", "db_config": None, "recent_days": 1},
]


def build_items(raw_items, item_shop_name, item_id, stat_day):
    """补充标题优化搜索词明细的商品、店铺、日期和唯一 key。"""
    result = []
    for item in raw_items:
        keyword = str(item.get("搜索词", "")).strip()
        if not keyword:
            continue
        item.update(
            {
                "店铺名称": item_shop_name,
                "日期类型": "day",
                "统计日期": stat_day,
                "商品ID": item_id,
            }
        )
        item["key"] = (
            f"{item['统计日期']}_{item['商品ID']}_{item['日期类型']}_"
            f"{item['店铺名称']}_{keyword}"
        )
        result.append(item)
    return result


if __name__ == "__main__":

    shop_name_list = [shop_config["shop_name"] for shop_config in SHOP_CONFIGS]
    shop_config_by_name = {shop_config["shop_name"]: shop_config for shop_config in SHOP_CONFIGS}
    recent_days = max(shop_config["recent_days"] for shop_config in SHOP_CONFIGS)
    table_name = "tb_sycm_商品_商品360_标题优化_搜索词_202504"  # noqa
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
        GoodObj = Goods(cookie)
        items_id = shop_item_ids.get(shop_name, [])
        if not items_id:
            logger.warning(f"{shop_name} 未配置商品ID，跳过")
            continue
        for item_id in items_id:
            for day in crawl_day_list:
                logger.info(f"正在采集{shop_name},item_id：{item_id},{day}的数据")
                dateRange = f"{day}|{day}"
                items = GoodObj.goods_360__title_drainage_excel(dateRange, item_id)
                items = build_items(items or [], shop_name, item_id, day)
                if not items:
                    logger.warning(f"{shop_name},item_id：{item_id},{day} 标题优化数据为空，跳过入库")
                    continue

                with DBManager(db_config=db_config) as db_manager:
                    db_manager.update_insert_data(items, table_name, "key")
                logger.info(f"{shop_name},item_id：{item_id},{day}的数据已入库")
                logger.info("-" * 100)
        logger.info(f"\n{'*' * 120}")


# python tb_sycm_商品_商品360_标题优化_搜索词_202504.py --start-date=2025-05-01 --end-date=2025-05-11 # noqa
