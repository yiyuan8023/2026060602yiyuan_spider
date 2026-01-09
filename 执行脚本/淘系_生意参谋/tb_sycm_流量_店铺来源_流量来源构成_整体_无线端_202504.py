
from API.API_ShengCan import Flow
from extra.db_manager import DBManager
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date

if __name__ == '__main__':

    shop_name_list = ['林内官方旗舰店']  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "tb_sycm_流量_店铺来源_流量来源构成_整体_无线端_202504" # NOQA
    site = '淘系_生意参谋'
    shop_cookies, crawl_day_list = select_shop_date(table_name, site, shop_name_list, 3)

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]
        FlowObj = Flow(cookie)
        for day in crawl_day_list:
            logger.info(f"正在采集{shop_name},{day}的数据")
            items = FlowObj.shop_from__flow_from_build_day(day)
            for item in items:
                item.update({
                    "店铺名称": shop_name,
                    "渠道": "无线",
                    "统计日期": day,
                    "日期类型": "day",
                })
                item[
                    "key"] = f"无线_{item['店铺名称']}_{day}_{item['日期类型']}_{item['一级来源']}_{item['二级来源']}_{item['三级来源']}"

            DBManager().update_insert_data(items, table_name, primary_key='key')
            logger.info(f"{shop_name},{day}的数据已入库")
            logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")

# python tb_sycm_流量_店铺来源_流量来源构成_整体_无线端_202504.py --start-date=2025-03-27 --end-date=2025-04-18 # NOQA
