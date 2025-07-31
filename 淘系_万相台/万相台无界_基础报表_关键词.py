# -*- coding: utf-8 -*-
# Author: Shao0000
# Date: 2025-04-21
# Time: 10:40
# Project: jide
# File: 万相台无界_基础报表_宝贝主体
from time import sleep

import pandas as pd

from WanXiangTaiApi.WanXiangTaiReport import WanXiangTaiReportApi
from db import DB
from extra_excel import read_download_zip
from logger_ import logger


def delete_history_data(df):
    # 将日期列转换为 datetime 类型
    df["日期"] = pd.to_datetime(df["日期"])

    # 获取日期区间的最小值和最大值
    min_date = df["日期"].min()
    max_date = df["日期"].max()
    print(min_date, max_date)
    sql = f"DELETE FROM `{table_name}` WHERE `日期` BETWEEN '{min_date}' AND '{max_date}' and `店铺名称`='{shop_name}';"
    db_obj.do_sql(sql)


if __name__ == '__main__':
    logger.info("*" * 100)
    logger.info("开始采集：万相台无界_基础报表_关键词")
    db_obj = DB()
    cookies_ = db_obj.do_select_cookies("生意参谋")
    table_name = "tb_tg_万相台无界_基础报表_关键词_202504"
    for i in cookies_:
        cookie = i[1]
        # cookie = '_tb_token_=b8f0d703-2e1c-4387-9dd8-3d2aea55b819; dnk=; t=61f6d9516106249f280ae435a10c9a79; lgc=; wk_cookie2=1de33e37072f0ef696f0385c1905c161; _tb_token_=313e8b0136b3; wk_unb=UoH%2B4NPsNoWZlw%3D%3D; cookie2=154930697d8a50696d572651f93a5a2b; _nk_=; cna=QpKMIIUcNlICASeqbVq05Ozi; xlly_s=1; uc1=cookie14=UoYajlesvxuitQ%3D%3D&cookie21=W5iHLLyFfoaZ; lid=%E6%9E%97%E5%86%85%E5%8E%A8%E7%94%B5%E6%97%97%E8%88%B0%E5%BA%97%3A%E4%B8%80%E5%85%83; unb=2212373938588; sgcookie=E100eK9lKaPAvPh32Rhx0Wrk22pCjCjkxB5bozkp8amFcgczA32rvWtf1NHfxUu2ojxtBs783DIwl9uxSO34BRayC0%2Bb7lIdr%2FyMhdwJdjXBG549bamGOo6ypc%2B71miUKwlv; cancelledSubSites=empty; csg=2f4422ce; sn=%E6%9E%97%E5%86%85%E5%8E%A8%E7%94%B5%E6%97%97%E8%88%B0%E5%BA%97%3A%E4%B8%80%E5%85%83; tfstk=gIft2V63QkqMejOus5wnnvAtOfUh7sQadG7SinxihMIdAMXMhRS0MsIcvPJbbCfAvGjhiOcclqLfxM1_WC9mMZsCojx1IncAM9_XohbMsENAAMjv3P-DcnIclO43Z7bN7IRXDuVuZ4UTIMIthITblvTkPyY6heqZTIRbqkDnGdPJgG69dUBfRyLDoAM1cfTBOH8SCVsXfpiByURXcisXOpT2knGjGEiBAH8XGnsXGydINpD90x-jMTJwuYLzsofdO6L9B3_LUYDz9KokJNtKGj92TdHG5HhjG6BvdSTMf8uH0CxNJFI4afR6Ht1MO1ZQGQ6PvspWw-4wCZBd0CfQlAt5IGAC1T3jGwd9cgCHpcEpV17CaB93NzQCTGbN9Z0bGejkAN56M7ay6Ct69e50YftAdt1MQIo_Dn5dR16A4uflwYHSq3LmCyUK3xJ68uEkuOSKzayMJ34h-xk2K8TpqyUK3xJ68eKu-3Dq3p25.'
        shop_name = i[0]
        WanXiangTaiReportObj = WanXiangTaiReportApi(cookie)
        task_id = WanXiangTaiReportObj.keyword_report__main_data_details()
        sleep(60 * 3)
        # task_id = '10568864'
        download_url = WanXiangTaiReportObj.get_download_url(task_id)
        if download_url:
            df = read_download_zip(download_url)
            df["日期"] = pd.to_datetime(df["日期"], errors='coerce')
            delete_history_data(df)
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
                })
            # print(items)
            db_obj.do_insert(items, table_name)
            # 删除历史数据
