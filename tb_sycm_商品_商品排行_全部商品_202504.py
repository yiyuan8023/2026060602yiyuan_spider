import sys

from ShengCanApi.goods import Goods
from database_manager import DatabaseManager
from extra_parser import parser_main
from logger_ import logger
from extra_date import get_date_range,get_recent_days


if __name__ == '__main__':
    table_name = "tb_sycm_商品_商品排行_全部商品_202504"
    logger.info("*" * 100)
    logger.info(f"开始采集：{table_name}")
    logger.info(f"接收到的命令行参数: {sys.argv}")

    start_date, end_data ,shop_name = parser_main()
    logger.info(f"解析得到的日期: start_date={start_date}, end_data={end_data},shop_name = {shop_name}")
    print()

    if start_date:
        crawl_day_list = get_date_range(start_date, end_data)
        # logger.info(f"解析参数{start_date}-{end_data}，即采集列表{crawl_day_list}")
    else:
        crawl_day_list = get_recent_days(3)  # 默认采集最近三天的数据


    if shop_name:
        shop_name_list = [shop_name]
    else:
        shop_name_list  =['林内官方旗舰店'] # 默认采集店铺

    logger.info(f"采集日期列表{crawl_day_list},采集店铺{shop_name_list}")

    for shop_name in shop_name_list:
        cookies_ = DatabaseManager().do_select_cookies("生意参谋",shop_name)
        for i in cookies_:
            cookie = i[1]
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

    # python 生参商品排行_全部商品.py --start-date=2025-06-27 --end-date=2025-06-29  --shop-name = '林内官方旗舰店'
