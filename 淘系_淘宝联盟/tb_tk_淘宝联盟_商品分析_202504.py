# File: 淘宝联盟_商品分析

from time import sleep

from Api_TaoBaoLianMeng.TaoKeGoodAnalysisApi import TaoKeGoodAnalysisApi
from extra.data_collector import data_collector
from extra.database_manager import DatabaseManager
from extra.logger_ import logger

if __name__ == "__main__":

    shop_name_list = ['林内热水器旗舰店']  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "tb_tk_淘宝联盟_商品分析_202504"
    site = '淘宝联盟'  # noqa
    name_suffix = "商品分析"
    shop_cookies, crawl_day_list = data_collector(table_name, site, shop_name_list, 1)

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]
        Obj = TaoKeGoodAnalysisApi(cookie, name_suffix=name_suffix)
        task_status_list_res = Obj.goods_task_status_list()  # 任务状态列表json数据包
        finish_task, un_finish_task = Obj.get_task_status_list(
            task_status_list_res=task_status_list_res)  # 解析数据包, 获取任务状态id
        # print(finish_task,un_finish_task)

        for day in crawl_day_list:
            # 调用create_task函数创建,下载任务
            Obj.create_goods_analysis_task(start_time=day, end_time=day, finish_task=finish_task)

        date_finish = []  # 已完成的日期列表
        count = 0

        while True:

            if len(date_finish) < len(crawl_day_list):
                if count > 0:
                    sleep(30)

                # 计算待采集的日期列表（从需要采集的日期中排除已完成的日期）
                remaining_days = list(set(crawl_day_list) - set(date_finish))

                logger.info(f"待采集{remaining_days}")
                for remaining_day in remaining_days:

                    logger.info(f"\n{'=' * 120}\n正在采集{shop_name}，{remaining_day}的数据")
                    finish_id = Obj.get_finish_id(start_time=remaining_day, end_time=remaining_day)
                    # print(id)
                    if finish_id:
                        # 获取报表下载链接
                        items = Obj.fetch_goods_file_link(finish_id)

                        for item in items:
                            item.update({
                                "店铺名称": shop_name,
                                "统计日期": remaining_day,
                                "计划类型": "全部推广类型"
                            })
                            item["key"] = f"{item['商品ID']}_{item['店铺名称']}_{item['计划类型']}_{item['统计日期']}"
                        # print(items)

                        DatabaseManager().upsert_data(items, table_name, primary_key='key')
                        date_finish.append(i)
                count = count + 1

            else:
                break

        logger.info(f"{shop_name_list},{crawl_day_list}已入库")
        logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")

# python tb_tk_淘宝联盟_商品分析_202504.py --start-date=2025-03-27 --end-date=2025-04-18
