# File: 万相台无界_基础报表_宝贝主体
from time import sleep

import pandas as pd

from API.API_WanXiangTai import WanXiangTaiReportApi
from extra.data_collector import data_collector
from extra.database_manager import DatabaseManager
from extra.downloader import Downloader
from extra.extra_date import get_time_ago
from extra.logger_ import logger


def delete_history_data(df):
    # 删除历史数据, 将日期列转换为 datetime 类型

    df["日期"] = pd.to_datetime(df["日期"])

    # 获取日期区间的最小值和最大值
    min_date = df["日期"].min()
    max_date = df["日期"].max()
    print(min_date, max_date)
    sql = f"DELETE FROM `{db_table_name}` WHERE `日期` BETWEEN '{min_date}' AND '{max_date}' and `店铺名称`='{shop_name}';"  # noqa
    DatabaseManager().execute_sql(sql)


if __name__ == '__main__':
    shop_name_list = ['林内官方旗舰店']  # 默认采集店铺,如果为[],则采集所有店铺
    db_table_name = "tb_tg_万相台无界_基础报表_人群报表_202504"
    site = '淘系_生意参谋'
    shop_cookies, crawl_day_list = data_collector(db_table_name, site, shop_name_list, 1)

    end_data = get_time_ago(0, 'days', crawl_day_list[0])
    start_data = get_time_ago(30, 'days', crawl_day_list[0])
    logger.info(f"采集日期区间{start_data}_{end_data}")

    for i in shop_cookies:
        cookie = i[1]

        shop_name = i[0]
        Obj = WanXiangTaiReportApi(cookie)
        task_id = Obj.crowd_report__main_data_details(start_data, end_data)
        sleep(60 * 3)
        # task_id = '10568864'
        download_url = Obj.get_download_url(task_id)

        if download_url:
            df = Downloader(download_url).download_zip()  # 下载zip文件,并读取csv文件

            # 将DataFrame中的"日期"列转换为datetime类型，并处理可能的错误值
            df["日期"] = pd.to_datetime(df["日期"], errors='coerce')

            # 将日期列格式化为字符串
            df["日期"] = df["日期"].dt.strftime('%Y-%m-%d')
            df_filled = df.fillna("")

            if df_filled.empty:
                items = {}
            else:
                items = df_filled.to_dict('records')

            for item in items:
                item.update({
                    "店铺名称": shop_name,
                    "归因周期": 15,
                })

            try:
                # 先插入2条数据,测试能不能成功，能成功再删除，重新插入新数据
                DatabaseManager().upsert_data(items[:2], db_table_name)
                delete_history_data(df)
                DatabaseManager().upsert_data(items, db_table_name)
            except Exception as e:
                logger.error(e)
