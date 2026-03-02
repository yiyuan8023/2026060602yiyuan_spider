from API.API_JingDong.API_Jdsz_ReportAPI import JdszReportAPI
from extra.db_manager import DBManager
from extra.extra_date import get_date_min_max
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date

if __name__ == "__main__":
    db_config = None  # noqa
    # db_config = "rinnai_py"  # noqa
    shop_name_list = ["BMW官方旗舰店"]  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "jd_jdsz_报表_新建报表_店铺_202509"
    site = "京东商智"
    shop_cookies, crawl_day_list = select_shop_date(table_name, site, shop_name_list, 7)
    min_date, max_date = get_date_min_max(crawl_day_list)

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]
        Obj = JdszReportAPI(cookie)
        logger.info(f"正在采集【{shop_name}】,{min_date}至{min_date}数据")
        items = Obj.sz_api_self_help_analysis_export_preview_list(min_date, max_date)

        for item in items:
            item.update(
                {
                    "店铺名称": shop_name,
                    # "日期类型": "day",
                }
            )
            item["key"] = f"{item['日期']}_{item['店铺名称']}"

        # print(items)
        # print(items[0].keys())
        DBManager().update_insert_data(items, table_name, primary_key="key")
        logger.info(f"{shop_name},{crawl_day_list}的数据已入库")
        logger.info("-" * 100)
logger.info(f"\n{'*' * 120}")

# python 生参商品排行_全部商品.py --start-date=2025-06-27 --end-date=2025-06-29  --shop-name = '林内官方旗舰店'
