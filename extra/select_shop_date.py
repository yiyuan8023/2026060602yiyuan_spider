import sys
from typing import Union, List

from database import DBManager
from extra.extra_parser import parser_main
from extra.logger_ import logger
from extra.extra_date import (
    get_date_range,
    get_recent_days,
    get_recent_months_first_day,
    get_unique_month_first_days,
)


def select_shop_date(
    db_table_name: Union[str, List[str]],
    site: str = "淘系_生意参谋",
    shop_name_list=None,
    recent_period: int = 3,
    period_type: str = "day",
):
    """
    统一生成采集店铺 Cookie 和采集日期列表。

    命令行参数优先级高于函数默认值，便于同一执行脚本支持临时补数。

    Args:
        db_table_name: 数据库表名
        site (str): 站点名称
        shop_name_list (list, optional): 店铺名称列表，默认为None(所有店铺)
        recent_period (int): 默认采集周期数，默认为3（最近3天或3个月）
        period_type (str): 周期类型，'day_'表示天，'month_'表示月，默认为'_day_'

    Returns:
        tuple: (shop_cookies, crawl_day_list)
            - shop_cookies: 包含店铺cookie信息的列表
            - crawl_day_list: 需要采集的日期列表
    """

    if shop_name_list is None:
        shop_name_list = []
    logger.info(f"\n{'*' * 120}")
    logger.info(f"开始采集：{db_table_name}")
    logger.info(f"接收到的命令行参数: {sys.argv}")

    # 命令行可临时覆盖日期范围和店铺，最终执行脚本无需重复写解析逻辑。
    start_date, end_data, shop_names = parser_main()
    # logger.info(f"解析得到的日期: start_date={start_date}, end_data={end_data},shop_names = {shop_names}")

    # 根据参数确定采集日期列表
    if start_date:
        # 如果命令行指定了日期，则使用指定的日期范围
        date_range = get_date_range(start_date, end_data)
        if period_type == "month":
            # 对于月份类型，获取日期范围内的所有月初日期并去重
            crawl_day_list = get_unique_month_first_days(date_range)
        else:
            # 对于天类型，直接使用日期范围
            crawl_day_list = date_range
    else:
        # 如果没有指定日期，则根据period_type使用默认的近期日期
        if period_type == "month":
            crawl_day_list = get_recent_months_first_day(recent_period)
        else:
            crawl_day_list = get_recent_days(recent_period)

    # shop_names 来自命令行，优先级高于脚本内默认店铺列表。
    if shop_names:
        shop_name_list = shop_names
    else:
        shop_name_list = shop_name_list

    logger.info(f"采集日期列表{crawl_day_list},采集店铺{shop_name_list}")

    # 空店铺列表表示采集该站点全部店铺；非空列表由 repository 参数化查询。
    if shop_name_list:
        shop_cookies = DBManager().select_cookies_shop(site, shop_name_list)
    else:
        shop_cookies = DBManager().select_cookies_all(site)

    # 返回店铺cookies和采集日期列表
    return shop_cookies, crawl_day_list


if __name__ == "__main__":
    _shop_name_list = ["林内官方旗舰店"]  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "tb_sycm_自助分析_取数_商品_流量来源_所有商品_格式化_202507"  # NOQA
    _site = "生意参谋"

    shop_cookiesA, crawl_day_listA = select_shop_date(
        table_name, _site, _shop_name_list, 3
    )
    # print(shop_cookiesA)
