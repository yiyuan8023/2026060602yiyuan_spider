from API.API_ShengCan import Flow

from extra.data_collector import data_collector
from extra.database_manager import DatabaseManager
from extra.logger_ import logger

if __name__ == '__main__':
    shop_name_list = ['林内官方旗舰店', '林内厨电旗舰店']  # 默认采集店铺,如果为[],则采集所有店铺
    # shop_name_list  =['林内品牌折扣店'] # 默认采集店铺,如果为[],则采集所有店铺
    # shop_name_list  =None # 默认采集店铺,如果为[],则采集所有店铺
    db_table_name = [
        'tb_sycm_流量_店铺来源_流量来源构成_全店_全店流量来源_202504', # noqa
        'tb_sycm_流量_店铺来源_流量来源构成_全店_经营优势来源渠道_202504', # noqa
        'tb_sycm_流量_店铺来源_流量来源构成_全店_分载体流量来源_202504', # noqa
    ]

    site = '淘系_生意参谋'

    shop_cookies, crawl_day_list = data_collector(db_table_name, site, shop_name_list, 1)

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]
        FlowObj = Flow(cookie)
        for day in crawl_day_list:
            logger.info(f"正在采集{shop_name},{day}的数据")
            items_dict = FlowObj.shop_from__flow_from_build__shop_flow_day(day)
            for sheet_name, items in items_dict.items():
                if sheet_name == '分载体流量来源':
                    for item in items:
                        item.update({
                            "sheet_name": sheet_name,
                            "店铺名称": shop_name,
                            "统计日期": day,
                            "日期类型": "day",
                        })
                        item["key"] = (f"{item['店铺名称']}_{day}_day_{item['流量载体']}_"
                                       f"{item['一级来源']}_{item['二级来源']}_{item['三级来源']}")
                    DatabaseManager().upsert_data(items, db_table_name[2], primary_key="key")

                if sheet_name == '经营优势来源渠道':
                    for item in items:
                        item.update({
                            "sheet_name": sheet_name,
                            "店铺名称": shop_name,
                            "统计日期": day,
                            "日期类型": "day",
                        })
                        item["key"] = f"{item['店铺名称']}_{day}_day_{item['流量载体']}_{item['来源名称']}"
                    DatabaseManager().upsert_data(items, db_table_name[1], primary_key="key")

                if sheet_name == '全店流量来源':
                    for item in items:
                        item.update({
                            "sheet_name": sheet_name,
                            "店铺名称": shop_name,
                            "统计日期": day,
                            "日期类型": "day",
                        })
                        item["key"] = (f"{item['店铺名称']}_{day}_day_{item['流量载体']}_"
                                       f"{item['一级来源']}_{item['二级来源']}_{item['三级来源']}")
                    DatabaseManager().upsert_data(items, db_table_name[0], primary_key="key")

            logger.info(f"{shop_name},{day}的数据已入库")
            logger.info("-" * 100)
        logger.info(f"\n{'*' * 120}")

# python tb_sycm_流量_店铺来源_流量来源构成_全店流量_新版.py --start-date=2025-03-27 --end-date=2025-04-18 # noqa
