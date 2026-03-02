from API.API_ShengCan import Goods
from extra.select_shop_date import select_shop_date
from extra.db_manager import DBManager
from extra.logger_ import logger

if __name__ == "__main__":

    shop_name_list = [
        "林内官方旗舰店",
        "林内厨电旗舰店",
    ]  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "tb_sycm_商品_商品360_标题优化_搜索词_202504"  # noqa
    site = "淘系_生意参谋"
    shop_cookies, crawl_day_list = select_shop_date(table_name, site, shop_name_list, 1)

    shop_item_ids = {
        "林内官方旗舰店": ["684257114535", "710970001756", "772238538685"],
        "林内厨电旗舰店": ["673717490518"],
    }

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]
        GoodObj = Goods(cookie)
        items_id = shop_item_ids.get(shop_name)
        for item_id in items_id:
            for day in crawl_day_list:
                logger.info(f"正在采集{shop_name},item_id：{item_id},{day}的数据")
                dateRange = f"{day}|{day}"
                items = GoodObj.goods_360__title_drainage_excel(dateRange, item_id)
                if items:
                    for item in items:
                        item.update(
                            {
                                "店铺名称": shop_name,
                                "日期类型": "day",
                                "统计日期": day,
                                "商品ID": item_id,
                            }
                        )
                        item["key"] = (
                            f"{item['统计日期']}_{item['商品ID']}_{item['日期类型']}_{item['店铺名称']}_{item['搜索词']}"
                        )
                    DBManager().update_insert_data(items, table_name, "key")
                    logger.info(f"{shop_name},item_id：{item_id},{day}的数据已入库")
                    logger.info("-" * 100)
        logger.info(f"\n{'*' * 120}")


# python tb_sycm_商品_商品360_标题优化_搜索词_202504.py --start-date=2025-05-01 --end-date=2025-05-11 # noqa
