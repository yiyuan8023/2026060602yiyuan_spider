
import sys
from database_manager import DatabaseManager
from extra_parser import parser_main
from logger_ import logger
from extra_date import get_date_range,get_recent_days


def data_collector(table_name: str,
                   site: str ='生意参谋',
                   shop_name_list = None,
                   recent_days: int = 3
                   ):
    """
      数据采集器函数，用户获取要采集的店铺和采集日期

      Args:
          table_name (str): 数据库表名
          site (str): 站点名称
          shop_name_list (list, optional): 店铺名称列表，默认为None(所有店铺)
          recent_days (int): 默认采集天数，默认为3天

      Returns:
          tuple: (shop_cookies, crawl_day_list)
              - shop_cookies: 包含店铺cookie信息的列表
              - crawl_day_list: 需要采集的日期列表
      """

    # 记录开始采集日志
    if shop_name_list is None:
        shop_name_list = []
    logger.info("*" * 100)
    logger.info(f"开始采集：{table_name}")
    logger.info(f"接收到的命令行参数: {sys.argv}")

    # 解析命令行参数获取日期范围和店铺名称
    start_date, end_data ,shop_names = parser_main()
    # logger.info(f"解析得到的日期: start_date={start_date}, end_data={end_data},shop_names = {shop_names}")

    # 根据参数确定采集日期列表，# 如果命令行指定了日期，则使用指定的日期，# 否则默认采集最近3天的数据
    if start_date:
        crawl_day_list = get_date_range(start_date, end_data)
        # logger.info(f"解析参数{start_date}-{end_data}，即采集列表{crawl_day_list}")
    else:
        crawl_day_list = get_recent_days(recent_days)

    # 确定需要采集的店铺列表，如果命令行指定了店铺，则使用指定的店铺列表，如果函数参数提供了店铺列表，则使用该列表
    if shop_names:
        shop_name_list = shop_names
    else:
        shop_name_list  = shop_name_list

    # 格式化店铺名称用于SQL查询
    shop_names = f'''  ('{"','".join(shop_name_list )}') '''
    logger.info(f"采集日期列表{crawl_day_list},采集店铺{shop_name_list}")



    # 如果店铺列表不为空，获取该站点指定店铺的cookies，如果为None则获取所有店铺cookies，即采集所有店铺
    if  shop_name_list:
        shop_cookies = DatabaseManager().select_cookies_shop(site, shop_names)
    else:
        shop_cookies = DatabaseManager().select_cookies_all(site)

    # 返回店铺cookies和采集日期列表
    return shop_cookies,crawl_day_list
