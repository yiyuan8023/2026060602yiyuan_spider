from API.API_ShengCan.Flow import Flow

from extra.select_shop_date import select_shop_date
from extra.db_manager import DBManager

from extra.logger_ import logger

if __name__ == "__main__":
    db_config = "rinnai_py"  # NOQA
    shop_name_list = ["林内热水器旗舰店"]  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "tb_sycm_流量_商品来源_商品来源流量_旧版_202504"  # NOQA
    site = "生意参谋"
    shop_cookies, crawl_day_list = select_shop_date(
        table_name, site, shop_name_list, 18
    )
    crawl_day_list = ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"]
    shop_item_ids = {
        "林内热水器旗舰店": [
            "732897762742",
            "793864718809",
            "763629523250",
            "763629523250",
            "1003352210602",
        ],
        # '林内厨电旗舰店': ["673717490518"]
    }

    for i in shop_cookies:
        cookie = i[1]
        print(cookie)
        shop_name = i[0]
        Obj = Flow(cookie)
        for day in crawl_day_list:
            item_ids = shop_item_ids.get(shop_name)
            for item_id in item_ids:
                logger.info(f"正在采集{shop_name},{day},{item_id}的数据")
                items = Obj.goods_from__listen_good_flow_day(item_id, day)
                if items:
                    for item in items:
                        item.update(
                            {
                                "商品id": item_id,
                                "店铺名称": shop_name,
                                "统计日期": day,
                                "日期类型": "day",
                            }
                        )
                        item["key"] = (
                            f"{item['商品id']}_{item['店铺名称']}_{day}_{item['日期类型']}_"
                            f"{item['一级来源']}_{item['二级来源']}_{item['三级来源']}"
                        )

                    # print(items)
                    DBManager(db_config=db_config).update_insert_data(
                        items, table_name, primary_key="key"
                    )

                    logger.info(f"{shop_name},{day}的数据已入库")
            logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")

# python tb_sycm_流量_商品来源_商品来源流量_旧版_202504.py --start-date=2025-03-27 --end-date=2025-04-18 # NOQA
