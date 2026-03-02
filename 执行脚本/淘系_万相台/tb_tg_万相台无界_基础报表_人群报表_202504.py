# File: 万相台无界_基础报表_宝贝主体
from time import sleep
import pandas as pd

from API.API_Wxt.WxtReport import WxtReportApi
from extra.select_shop_date import select_shop_date
from extra.db_manager import DBManager
from extra.downloader import Downloader
from extra.extra_date import get_time_ago, get_df_min_max_date, get_items_min_max_date
from extra.logger_ import logger

if __name__ == "__main__":
    shop_name_list = ["林内官方旗舰店"]  # 默认采集店铺,如果为[],则采集所有店铺
    db_table_name = "tb_tg_万相台无界_基础报表_人群报表_202504"
    site = "生意参谋"
    shop_cookies, crawl_day_list = select_shop_date(
        db_table_name, site, shop_name_list, 1
    )

    end_data = get_time_ago(0, "days", crawl_day_list[0])
    start_data = get_time_ago(30, "days", crawl_day_list[0])
    logger.info(f"采集日期区间{start_data}_{end_data}")

    for i in shop_cookies:
        cookie = i[1]

        shop_name = i[0]
        Obj = WxtReportApi(cookie)
        task_id = Obj.wxt_crowd_report(start_data, end_data)
        sleep(60 * 2)
        # task_id = '10568864'
        download_url = Obj.get_download_url(task_id)

        if download_url:
            items = Downloader(
                download_url
            ).download_zip()  # 下载zip文件,并读取csv文件 # NOQA
            for item in items:
                item.update(
                    {
                        "店铺名称": shop_name,
                        "归因周期": 15,
                    }
                )
            min_date, max_date = get_items_min_max_date(items, "日期")
            delete_sql = (
                f"delete from {db_table_name} where 店铺名称='{shop_name}' "  # noqa
                f"and `日期` between '{min_date}' and '{max_date}'"
            )  # noqa
            # 先删后入,没有key
            DBManager().insert_delete_insert_data(items, db_table_name, delete_sql)
