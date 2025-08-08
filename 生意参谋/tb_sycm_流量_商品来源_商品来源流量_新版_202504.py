from ShengCanApi.Flow import Flow
from extra.data_collector import data_collector
from extra.database_manager import DatabaseManager
from extra.logger_ import logger

if __name__ == '__main__':
    shop_name_list = ['林内官方旗舰店', '林内厨电旗舰店']  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "tb_sycm_流量_商品来源_商品来源流量_新版_202504"  # noqa
    site = '生意参谋'
    shop_cookies, crawl_day_list = data_collector(table_name, site, shop_name_list, 1)

    shop_item_ids = {
        '林内官方旗舰店': ["684257114535", "710970001756", "772238538685"],
        '林内厨电旗舰店': ["673717490518"]
    }

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]
        FlowObj = Flow(cookie)
        for day in crawl_day_list:
            item_ids = shop_item_ids.get(shop_name)
            for item_id in item_ids:
                logger.info(f"正在采集{shop_name},{day},{item_id}的数据")
                items1, items2 = FlowObj.goods_from__listen_good_flow_day_new(item_id, day)

                for items in [items1, items2]:
                    for item in items: # noqa
                        item.update({
                            "商品id": item_id,
                            "店铺名称": shop_name,
                            "统计日期": day,
                            "日期类型": "day",
                        })
                        item["key"] = (f"{item['商品id']}_{item['店铺名称']}_{day}_{item['日期类型']}_"
                                       f"{item['一级来源']}_{item['二级来源']}_{item['三级来源']}")
                    # print(items)
                    DatabaseManager().upsert_data(items, table_name, primary_key="key")

            logger.info(f"{shop_name},{day}的数据已入库")
            logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")

# python tb_sycm_流量_商品来源_商品来源流量_新版_202504.py --start-date=2025-03-27 --end-date=2025-04-18 # noqa
