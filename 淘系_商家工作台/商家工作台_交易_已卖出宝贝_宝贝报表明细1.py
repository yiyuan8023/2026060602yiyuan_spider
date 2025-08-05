
from TiaoMaoMySellerApi.MysellerTrade import MySellerTradeAPI
from extra.data_collector import data_collector
from extra.database_manager import DatabaseManager
from extra.extra_date import get_min_max_timestamps
from extra.logger_ import logger

if __name__ == '__main__':

    shop_name_list = ['林内官方旗舰店']  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "tb_商家工作台_交易_已卖出宝贝_宝贝报表明细_202504"
    site = '生意参谋'
    shop_cookies, crawl_day_list = data_collector(table_name, site, shop_name_list, 3)
    start_timestamp, end_timestamp = get_min_max_timestamps(crawl_day_list)

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]
        Obj = MySellerTradeAPI(cookie)  # 创建对象
        items = Obj.taobao_list_export_order(start_timestamp, end_timestamp)
        for item in items:
            item.update({
                "店铺名称": shop_name,
            })

        DatabaseManager().upsert_data(items, table_name, primary_key='子订单编号')
        logger.info("-" * 100)
    logger.info("*" * 100)
