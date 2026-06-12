from API.API_TaoXi_SYCM import Goods  # noqa
from extra.select_shop_date import select_shop_date
from database import DBManager
from extra.logger_ import logger

SHOP_CONFIGS = [
    {"shop_name": "林内官方旗舰店", "db_config": None, "recent_days": 1},
    {"shop_name": "林内厨电旗舰店", "db_config": None, "recent_days": 1},
]


def build_items(raw_items, item_shop_name, stat_day):
    """补充推荐内容明细的店铺、日期和唯一 key。"""
    result = []
    for item in raw_items:
        video_id = str(item.get("视频id", "")).strip()
        if not video_id:
            continue
        item.update(
            {
                "店铺名称": item_shop_name,
                "日期类型": "day",
                "统计日期": stat_day,
            }
        )
        item["key"] = f"{item['店铺名称']}_{item['统计日期']}_{item['日期类型']}_{video_id}"
        result.append(item)
    return result


if __name__ == "__main__":

    shop_name_list = [shop_config["shop_name"] for shop_config in SHOP_CONFIGS]
    shop_config_by_name = {shop_config["shop_name"]: shop_config for shop_config in SHOP_CONFIGS}
    recent_days = max(shop_config["recent_days"] for shop_config in SHOP_CONFIGS)
    db_table_name = (
        "tb_sycm_内容_渠道效果_推荐_单条效果_微详情视频_全部内容_202507"  # noqa
    )
    site = "淘系_生意参谋"
    shop_cookies, crawl_day_list = select_shop_date(
        db_table_name, site, shop_name_list, recent_days
    )

    for shop_cookie in shop_cookies:
        cookie = shop_cookie[1]
        shop_name = shop_cookie[0]
        db_config = shop_config_by_name.get(shop_name, {}).get("db_config")
        GoodObj = Goods(cookie)
        for day in crawl_day_list:
            logger.info(f"正在采集{shop_name}，{day}的数据")

            items = GoodObj.recommend_analysis_single_excel(day)
            items = build_items(items or [], shop_name, day)
            if not items:
                logger.warning(f"{shop_name},{day} 推荐单条效果数据为空，跳过入库")
                continue

            with DBManager(db_config=db_config) as db_manager:
                db_manager.update_insert_data(items, db_table_name, primary_key="key")
            logger.info(f"{shop_name},{day}的数据已入库")
        logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")

# python tb_sycm_内容_渠道效果_推荐_单条效果_微详情视频_全部内容_202507.py --start-date=2025-04-17 --end-date=2025-07-16 # noqa
