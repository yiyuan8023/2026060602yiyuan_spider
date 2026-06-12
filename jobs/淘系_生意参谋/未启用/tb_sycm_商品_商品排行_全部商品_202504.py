from API.API_TaoXi_SYCM import Goods  # noqa
from database import DBManager
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date

SHOP_CONFIGS = [
    {"shop_name": "林内官方旗舰店", "db_config": None, "recent_days": 1},
    {"shop_name": "林内厨电旗舰店", "db_config": None, "recent_days": 1},
]


def build_items(raw_items, item_shop_name):
    """补充商品排行明细的店铺、日期类型和唯一 key。"""
    result = []
    for item in raw_items:
        stat_day = str(item.get("统计日期", "")).strip()
        item_id = str(item.get("商品ID", "")).strip()
        if not stat_day or not item_id:
            continue
        item.update(
            {
                "店铺名称": item_shop_name,
                "日期类型": "day",
            }
        )
        item["key"] = f"{item['统计日期']}_{item_id}_{item['日期类型']}_{item['店铺名称']}"
        result.append(item)
    return result


if __name__ == "__main__":
    shop_name_list = [shop_config["shop_name"] for shop_config in SHOP_CONFIGS]
    shop_config_by_name = {shop_config["shop_name"]: shop_config for shop_config in SHOP_CONFIGS}
    recent_days = max(shop_config["recent_days"] for shop_config in SHOP_CONFIGS)
    table_name = "tb_sycm_商品_商品排行_全部商品_202504"  # noqa
    site = "生意参谋"
    shop_cookies, crawl_day_list = select_shop_date(table_name, site, shop_name_list, recent_days)
    for shop_cookie in shop_cookies:
        cookie = shop_cookie[1]
        shop_name = shop_cookie[0]
        db_config = shop_config_by_name.get(shop_name, {}).get("db_config")
        GoodObj = Goods(cookie)
        for day in crawl_day_list:
            logger.info(f"正在采集【{shop_name}】,{day}数据")
            items = GoodObj.good_rank__all_good_day(day)
            items = build_items(items or [], shop_name)
            if not items:
                logger.warning(f"{shop_name},{day} 商品排行数据为空，跳过入库")
                continue

            with DBManager(db_config=db_config) as db_manager:
                db_manager.update_insert_data(items, table_name, primary_key="key")
            logger.info(f"{shop_name},{day}的数据已入库")
            logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")

# python 生参商品排行_全部商品.py --start-date=2025-06-27 --end-date=2025-06-29  --shop-name = '林内官方旗舰店'
