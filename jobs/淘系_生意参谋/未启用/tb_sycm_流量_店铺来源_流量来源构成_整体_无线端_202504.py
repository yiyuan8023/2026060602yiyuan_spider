from API.API_TaoXi_SYCM import Flow  # noqa
from database import DBManager
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date

SHOP_CONFIGS = [
    {"shop_name": "林内官方旗舰店", "db_config": None, "recent_days": 3},
]


def build_items(raw_items, item_shop_name, stat_day):
    """补充店铺来源无线端流量维度，并生成唯一 key。"""
    result = []
    for item in raw_items:
        item.update(
            {
                "店铺名称": item_shop_name,
                "渠道": "无线",
                "统计日期": stat_day,
                "日期类型": "day",
            }
        )
        item["key"] = (
            f"无线_{item['店铺名称']}_{stat_day}_{item['日期类型']}_"
            f"{item['一级来源']}_{item['二级来源']}_{item['三级来源']}"
        )
        result.append(item)
    return result


if __name__ == "__main__":

    shop_name_list = [shop_config["shop_name"] for shop_config in SHOP_CONFIGS]
    shop_config_by_name = {shop_config["shop_name"]: shop_config for shop_config in SHOP_CONFIGS}
    recent_days = max(shop_config["recent_days"] for shop_config in SHOP_CONFIGS)
    table_name = "tb_sycm_流量_店铺来源_流量来源构成_整体_无线端_202504"  # noqa
    site = "淘系_生意参谋"
    shop_cookies, crawl_day_list = select_shop_date(table_name, site, shop_name_list, recent_days)

    for shop_cookie in shop_cookies:
        cookie = shop_cookie[1]
        shop_name = shop_cookie[0]
        db_config = shop_config_by_name.get(shop_name, {}).get("db_config")
        FlowObj = Flow(cookie)
        for day in crawl_day_list:
            logger.info(f"正在采集{shop_name},{day}的数据")
            items = FlowObj.shop_from__flow_from_build_day(day)
            items = build_items(items or [], shop_name, day)
            if not items:
                logger.warning(f"{shop_name},{day} 店铺来源无线端数据为空，跳过入库")
                continue

            with DBManager(db_config=db_config) as db_manager:
                db_manager.update_insert_data(items, table_name, primary_key="key")
            logger.info(f"{shop_name},{day}的数据已入库")
            logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")

# python tb_sycm_流量_店铺来源_流量来源构成_整体_无线端_202504.py --start-date=2025-03-27 --end-date=2025-04-18 # noqa
