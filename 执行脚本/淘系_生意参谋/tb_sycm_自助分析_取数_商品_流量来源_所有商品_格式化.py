import io
import random
from time import sleep

import requests

from API.API_ShengCan.SelfAnalysis import SelfAnalysis

from extra.select_shop_date import select_shop_date
from database import DBManager
from extra.downloader import Downloader
from extra.extra_date import get_date, get_date_range
from extra.logger_ import logger

if __name__ == "__main__":
    db_config = "rinnai_py"  # NOQA
    shop_name_id = {
        "林内官方旗舰店": "20893",
        # '林内热水器旗舰店': '20805'  # 暂时没有开通
    }

    shop_name_list = shop_name_id.keys()

    table_name = "tb_sycm_自助分析_取数_商品_流量来源_所有商品_格式化_202507"  # NOQA
    site = "生意参谋"
    shop_cookies, crawl_day_list = select_shop_date(table_name, site, shop_name_list, 3)
    # crawl_day_list = get_date_range('2026-03-26', '2026-03-26')
    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]
        shop_id = shop_name_id.get(shop_name)
        # print(shop_name, shop_id)
        Obj = SelfAnalysis(cookie)
        for day in crawl_day_list:
            sleep(random.uniform(0.5, 2))
            start_date = end_data = get_date(day)
            logger.info(f"正在采集{shop_name},{start_date}——{end_data}的数据")
            report_id = Obj.create_report(shop_id, start_date, end_data)
            # print(report_id)
            Obj.fetch_data_download(report_id)
            if report_id:
                logger.success(f"创建任务成功，{report_id}")
                file_url = None
                while True:
                    if not file_url:
                        logger.info("报表在生成中")
                        file_url = Obj.query_download_url(report_id)
                        sleep(2)
                    else:
                        logger.info("报表生成完成")
                        break
                items = Downloader(api=file_url, cookie=cookie).download_excel()

                for item in items:
                    item["key"] = (
                        f"{item['商品ID']}_{item['店铺名称']}_{item['统计日期']}_"
                        f"{item['一级流量来源']}_{item['二级流量来源']}_{item['三级流量来源']}"
                    )
                # print(items)
                DBManager(db_config=db_config).update_insert_data(
                    items, table_name, primary_key="key"
                )
                logger.info("-" * 100)
                logger.info(f"{shop_name},{day}的数据已入库")
            logger.info(f"\n{'*' * 120}")
    # requests.get("https://bi.bi-cheng.cn/public-api/data-source/t1972c38bbd0f4192a5fff8f/refresh?token=e4571cce418f946158c065bf")
#
# python tb_sycm_自助分析_取数_商品_流量来源_所有商品_格式化.py --start-date=2024-07-20 --end-date=2025-07-31
