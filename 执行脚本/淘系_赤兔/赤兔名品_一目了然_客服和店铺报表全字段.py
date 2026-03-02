from API.API_ChiTu import ChiTuClearAGlanceAPI
from API.API_ChiTu import ChituCookies
from db import DB
from extra_cookie import cookiejar_to_cookie_str
from extra_parser import parser_main
from extra_time import calculate_days_diff_with_range, get_date, split_date_range
from logger_ import logger


def fetch_customer_it(from_, to_):
    """
    一目了然》》勿删客服绩效
    """
    logger.info(f"开始爬取{shop_name} 一目了然》》勿删客服绩效 {from_}-{to_} 的数据")
    data = ChiTuClearAGlance.export_table("勿删客服绩效", from_, to_)
    items = []
    if data:
        for i in data:
            if i["旺旺"] == "汇总" or i["旺旺"] == "均值":
                pass
            else:
                i["店铺名称"] = shop_name
                i["统计日期"] = from_
                i["key"] = f'{shop_name}{i["旺旺"]}{from_}{i["旺旺昵称"]}'
                items.append(i)

        db_obj.do_insert(items, "tb_赤兔名品_一目了然_客服报表全字段_202507")


def fetch_shop_it(from_, to_):
    """
    一目了然》》勿删店铺绩效
    """
    logger.info(f"开始爬取{shop_name} 一目了然》》勿删店铺绩效 {from_}-{to_} 的数据")
    data = ChiTuClearAGlance.export_table("勿删店铺绩效", from_, to_)
    if data:
        items = []
        for i in data:
            if i["日期"] == "汇总" or i["日期"] == "均值":
                pass
            else:
                i["店铺名称"] = shop_name
                i["日期类型"] = "day"
                i["key"] = f'{shop_name}{i["日期"]}{i["日期类型"]}'
                items.append(i)
        db_obj.do_insert(items, "tb_赤兔名品_一目了然_店铺报表全字段_202507")


def chitu_clear_a_glance():
    """
    一目了然
    """
    # 一目了然 勿删_客服_it
    for days in crawl_day_list:
        from_ = to_ = get_date(days)
        fetch_customer_it(from_, to_)
        fetch_shop_it(from_, to_)
    # 一目了然 勿删_店铺_it
    # print(start_date,end_data)
    split_date_range_ = split_date_range(start_date, end_data)
    # print(split_date_range_)
    for i in split_date_range_:
        fetch_shop_it(from_=i[0], to_=i[1])


if __name__ == "__main__":
    CHITU_PASSWORD = {"小吉旗舰店": "xiaoji123"}
    logger.info("*" * 100)
    logger.info("开始采集：tb_赤兔名品_一目了然_客服和店铺报表全字段")
    start_date, end_data = parser_main()
    if start_date and end_data:
        crawl_day_list = calculate_days_diff_with_range(start_date, end_data)
        logger.info(f"解析参数{start_date}-{end_data}，即采集列表{crawl_day_list}")
    else:
        start_date = end_data = get_date(-1)
        crawl_day_list = [-1]
    db_obj = DB()
    cookies_ = db_obj.do_select_cookies_jar("淘系_生意参谋")
    # table_name = "tb_赤兔名品_一目了然_客服报表全字段_202504"
    for i in cookies_:
        shop_name = i[0]
        ChituCookies_obj = ChituCookies(shop_name, f"{i[1]}")
        cookie_res = ChituCookies_obj.main()

        if cookie_res["status"] == 1:
            cookie_str = cookiejar_to_cookie_str(cookie_res["content"])
            # 一目了然，初始化
            ChiTuClearAGlance = ChiTuClearAGlanceAPI(
                cookie_str, CHITU_PASSWORD[shop_name]
            )
            chitu_clear_a_glance()
        else:
            logger.error("赤兔的cookie生成失败")
# python 赤兔名品_一目了然_客服和店铺报表全字段.py --start-date=2025-01-01 --end-date=2025-05-05
