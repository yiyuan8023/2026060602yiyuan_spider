

from ShengCanApi.goods import Goods
from database_manager import DatabaseManager
from logger_ import logger
from data_collector import data_collector



if __name__ == '__main__':
    shop_name_list  =['林内官方旗舰店','林内厨电旗舰店'] # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "tb_sycm_商品_商品排行_全部商品_202504"
    site = '生意参谋'
    shop_cookies,crawl_day_list = data_collector(table_name,site,shop_name_list,1)

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]
        GoodObj = Goods(cookie)
        for day in crawl_day_list:
            logger.info(f"正在采集【{shop_name}】,{day}数据")
            items = GoodObj.good_rank__all_good_day(day)
            for item in items:
                item.update({
                    "店铺名称": shop_name,
                    "日期类型": "day",
                })
                item["key"] = f"{item['统计日期']}_{item['商品ID']}_{item['日期类型']}_{item['店铺名称']}"

            # print(items)
            # print(items[0].keys())
            DatabaseManager().upsert_data(items, table_name,primary_key= 'key')
            logger.info("-" * 100)
    logger.info("*" * 100)
# python 生参商品排行_全部商品.py --start-date=2025-06-27 --end-date=2025-06-29  --shop-name = '林内官方旗舰店'
