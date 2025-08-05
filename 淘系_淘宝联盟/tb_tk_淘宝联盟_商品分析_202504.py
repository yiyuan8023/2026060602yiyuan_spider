# File: 淘宝联盟_商品分析

from time import sleep

from TaoBaoLianMengApi.TaoKeDataAnalysisApi import TaoKeDataAnalysisApi
from extra.data_collector import data_collector
from extra.database_manager import DatabaseManager

from extra.logger_ import logger, Logger


def create_task(start_time, end_time):
    """
        创建淘宝联盟商品分析任务
        检查该时间段的报表是否已经存在且已完成，如果存在则直接返回任务ID；如果不存在则调用API
    创建新的报表任务。
    """
    logger.info(f"\n{'-' * 120}\n在创建 {start_time} 00:00:00~{end_time} 23:59:59-商品分析 报告")

    file_name = f"{start_time} 00:00:00~{end_time} 23:59:59-商品分析"
    if file_name in finish_task.keys():
        logger.info(f"报告已存在，且完成{file_name}")
        return finish_task[file_name]

    else:
        res_json = Obj.goods_analysis__goods_management(start_time, end_time)
        # print(res_json)
        if res_json and res_json.get('data'):
            id_list = res_json.get('data').get('idList')
            logger.info(f"任务已创建，{id_list}")
        else:
            logger.info("任务已经存在")


def get_finish_id(start_time, end_time):
    finish_task, un_finish_task = Obj.get_task_status_list()
    file_name = f"{start_time} 00:00:00~{end_time} 23:59:59-商品分析"
    if file_name in finish_task.keys():
        return finish_task[file_name]

    else:
        res_json = Obj.goods_analysis__goods_management(start_time, end_time)
        if res_json and res_json.get('data'):
            id_list = res_json.get('data').get('idList')
            logger.info(f"任务已创建，{id_list}")
            return None
        else:
            logger.info("任务已经存在")
            return None


if __name__ == "__main__":

    shop_name_list = ['林内热水器旗舰店']  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "tb_tk_淘宝联盟_商品分析_202504"
    site = '淘宝联盟'
    shop_cookies, crawl_day_list = data_collector(table_name, site, shop_name_list, 1)

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]
        Obj = TaoKeDataAnalysisApi(cookie)
        finish_task, un_finish_task = Obj.get_task_status_list()
        # print(finish_task,un_finish_task)

        for day in crawl_day_list:
            # 调用create_task函数创建,下载任务
            create_task(start_time=day, end_time=day)

        spider_finish = []
        count = 0

        while True:

            if len(spider_finish) < len(crawl_day_list):
                if count > 0:
                    sleep(30)

                # 计算待采集的日期列表（从需要采集的日期中排除已完成的日期）
                remaining_days = list(set(crawl_day_list) - set(spider_finish))

                logger.info(f"待采集{remaining_days}")
                for remaining_day in remaining_days:

                    logger.info(f"\n{'=' * 120}\n正在采集{shop_name}，{remaining_day}的数据")
                    finish_id = get_finish_id(start_time=remaining_day, end_time=remaining_day)
                    # print(id)
                    if finish_id:
                        # 获取报表下载链接
                        items = Obj.fetch_report_shop_data(finish_id)

                        for item in items:
                            item.update({
                                "店铺名称": shop_name,
                                "统计日期": remaining_day,
                                "计划类型": "全部推广类型"
                            })
                            item["key"] = f"{item['商品ID']}_{item['店铺名称']}_{item['计划类型']}_{item['统计日期']}"
                        # print(items)

                        DatabaseManager().upsert_data(items, table_name, primary_key='key')
                        spider_finish.append(i)
                count = count + 1

            else:
                break

        logger.info(f"{shop_name_list},{crawl_day_list}已完成")

# python tb_tk_淘宝联盟_商品分析_202504.py --start-date=2025-03-27 --end-date=2025-04-18
