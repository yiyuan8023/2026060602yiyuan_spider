from ShengCanApi.Flow import Flow
from database_manager import DB
from extra_parser import parser_main
from logger_ import logger
from extra_time import get_date, calculate_days_diff_with_range

if __name__ == '__main__':
    logger.info("*" * 100)
    logger.info("开始采集：tb_sycm_流量_店铺来源_流量来源构成_整体_无线端")
    start_date, end_data = parser_main()
    if start_date and end_data:
        crawl_day_list = calculate_days_diff_with_range(start_date, end_data)
        logger.info(f"解析参数{start_date}-{end_data}，即采集列表{crawl_day_list}")
    else:
        crawl_day_list = [-3,-2,-1]
    cookies_ = DB().do_select_cookies("生意参谋")
    for i in cookies_:
        cookie = i[1]
        shop_name = i[0]
        FlowObj = Flow(cookie)
        for days in crawl_day_list:
            logger.info(f"正在采集{shop_name}，{get_date(days)}的数据")
            items = FlowObj.shop_from__flow_from_build_day(days)
            for item in items:
                item.update({
                    "店铺名称": shop_name,
                    "渠道": "无线",
                    "统计日期": get_date(days),
                    "日期类型": "day",

                })
                item["key"] = f"无线_{item["店铺名称"]}_{get_date(days)}_{item["日期类型"]}_{item['一级来源']}_{item['二级来源']}_{item['三级来源']}"

            # print(items)
            DB().do_insert(items, "tb_sycm_流量_店铺来源_流量来源构成_整体_无线端_202504")


# python 生参店铺流量-旧版.py --start-date=2025-03-27 --end-date=2025-04-18