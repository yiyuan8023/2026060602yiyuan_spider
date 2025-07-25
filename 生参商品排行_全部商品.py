import sys

from ShengCanApi.goods import Goods
from db import DB
from extra_parser import parser_main
from logger_ import logger
from extra_time import get_date, calculate_days_diff_with_range

if __name__ == '__main__':
    logger.info("*" * 100)
    logger.info("开始采集：tb_sycm_商品_商品排行_全部商品")
    logger.info(f"接收到的命令行参数: {sys.argv}")

    start_date, end_data = parser_main()

    logger.info(f"解析得到的日期: start_date={start_date}, end_data={end_data}")
    print()
    if start_date and end_data:
        print(start_date, end_data)
        crawl_day_list = calculate_days_diff_with_range(start_date, end_data)
        logger.info(f"解析参数{start_date}-{end_data}，即采集列表{crawl_day_list}")
    else:
        crawl_day_list = [-3, -2, -1]  # 默认采集最近三天的数据

    cookies_ = DB().do_select_cookies("生意参谋")
    for i in cookies_:
        cookie = i[1]
        shop_name = i[0]
        GoodObj = Goods(cookie)
        for day in crawl_day_list:
            logger.info(f"正在采集{shop_name},{get_date(day)}的数据")
            items = GoodObj.good_rank__all_good_day(day)
            for item in items:
                item.update({
                    "店铺名称": shop_name,
                    "日期类型": "day",
                })
                item["key"] = f"{item['统计日期']}_{item['商品ID']}_{item['日期类型']}_{item['店铺名称']}"

            # print(items)
            # print(items[0].keys())
            DB().do_insert(items, "tb_sycm_商品_商品排行_全部商品_202504")

# python 生参商品排行_全部商品.py --start-date=2025-03-27 --end-date=2025-04-18
