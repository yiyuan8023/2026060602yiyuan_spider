import sys

from database import DBManager
from extra.extra_parser import parser_main
from extra.logger_ import logger


def cookie_collector(
    site: str = "生意参谋",
    shop_name_list=None,
):
    # 记录开始采集日志
    if shop_name_list is None:
        shop_name_list = []
    logger.info(f"\n{'*' * 120}")
    logger.info(f"开始获取cookie采集：{shop_name_list}")
    logger.info(f"接收到的命令行参数: {sys.argv}")

    # 解析命令行参数获取日期范围和店铺名称
    start_date, end_data, shop_names = parser_main()
    # logger.info(f"解析得到的日期: start_date={start_date}, end_data={end_data},shop_names = {shop_names}")

    # 确定需要采集的店铺列表，如果命令行指定了店铺，则使用指定的店铺列表，如果函数参数提供了店铺列表，则使用该列表
    if shop_names:
        shop_name_list = shop_names
    else:
        shop_name_list = shop_name_list

    logger.info(f"需要转换cookie店铺{shop_name_list}")
    # 如果店铺列表不为空，获取该站点指定店铺的cookies，如果为None则获取所有店铺cookies，即采集所有店铺
    if shop_name_list:
        shop_cookies = DBManager().select_cookies_shop(site, shop_name_list)
    else:
        shop_cookies = DBManager().select_cookies_all(site)

    # 返回店铺cookies
    return shop_cookies
