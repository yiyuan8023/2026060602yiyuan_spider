import sys

from ShengCanApi.goods import Goods
from database_manager import DatabaseManager
from extra_parser import parser_main
from logger_ import logger
from extra_time import get_date, calculate_days_diff_with_range
from extra_date import get_date_range,get_recent_days


if __name__ == '__main__':
    table_name = "tb_sycm_商品_商品排行_全部商品_202504"
    logger.info("*" * 100)
    logger.info(f"开始采集：{table_name}")
    logger.info(f"接收到的命令行参数: {sys.argv}")

    start_date, end_data = parser_main()

    logger.info(f"解析得到的日期: start_date={start_date}, end_data={end_data}")
    print()
    if start_date and end_data:
        print(start_date, end_data)
        crawl_day_list = get_date_range(start_date, end_data)
        logger.info(f"解析参数{start_date}-{end_data}，即采集列表{crawl_day_list}")
    else:
        crawl_day_list = get_recent_days(3)  # 默认采集最近三天的数据

    cookies_ = DatabaseManager().do_select_cookies("生意参谋")
    for i in cookies_:
        cookie = i[1]
        shop_name = i[0]
        GoodObj = Goods(cookie)
        for day in crawl_day_list:
            logger.info(f"正在采集{shop_name},{day}的数据")
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

# python 生参商品排行_全部商品.py --start-date=2025-06-27 --end-date=2025-06-29
