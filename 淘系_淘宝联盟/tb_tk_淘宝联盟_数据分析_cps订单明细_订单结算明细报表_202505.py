# File: 淘宝联盟_商品分析
# todo 只支持最近365天数据，一次最多可以采集31天数据

from time import sleep

from Api_TaoBaoLianMeng.TaoKe_cps_api import TaoKeCpsApi
from extra.data_collector import data_collector
from extra.database_manager import DatabaseManager
from extra.extra_date import get_date_min_max, split_date_range
from extra.logger_ import logger

if __name__ == "__main__":
    db_config = "rinnai_py"  # noqa

    shop_name_list = ['林内热水器旗舰店', '林内官方旗舰店']  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "tb_tk_淘宝联盟_数据分析_cps订单明细_订单结算明细报表_202505"
    site = '淘宝联盟'  # noqa
    name_suffix = "订单结算明细报表"
    shop_cookies, crawl_day_list = data_collector(table_name, site, shop_name_list, 1)
    min_date, max_date = get_date_min_max(crawl_day_list)  # 获取最小和最大时间

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]
        split_date = split_date_range(min_date, max_date)
        for date in split_date:
            start_time, end_time = date

            Obj = TaoKeCpsApi(cookie, start_time, end_time, name_suffix=name_suffix)
            Obj.tb_tk_cps_settlement_report()  # 创建任务
            # sleep(30)

            task_status_list_res = Obj.cps_task_status_list()  # 任务状态列表json数据包

            finish_task, un_finish_task = Obj.get_task_status_list(
                task_status_list_res=task_status_list_res)  # 解析数据包, 获取任务状态id

            print(un_finish_task)

            # 等待任务生成
            while un_finish_task:
                logger.info("等待30s")
                sleep(30)

                task_status_list_res = Obj.cps_task_status_list()  # 任务状态列表json数据包
                finish_task, un_finish_task = Obj.get_task_status_list(
                    task_status_list_res=task_status_list_res)  # 解析数据包, 获取任务状态id

                print(finish_task, un_finish_task)

            logger.info(f"\n{'=' * 120}\n开始采集{shop_name}，{start_time}_{end_time}的数据")
            report_name = f"{start_time} 00:00:00~{end_time} 23:59:59-{name_suffix}"
            report_id = finish_task.get(report_name)  # 获取报名名称对应的id
            items = Obj.fetch_cps_file_link(report_id)

            for item in items:
                item.update({
                    "店铺名称": shop_name,
                })
                # item["key"] = f"{item['商品ID']}_{item['店铺名称']}_{item['计划类型']}_{item['统计日期']}"

            DatabaseManager(db_config=db_config).upsert_data(items, table_name, primary_key='淘宝子订单编号')
    #
            logger.info(f"{shop_name},{start_time}_{end_time}已入库")
        logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")

# python tb_tk_淘宝联盟_商品分析_202504.py --start-date=2025-03-27 --end-date=2025-04-18
