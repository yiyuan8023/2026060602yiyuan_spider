# File: 淘宝联盟_商品分析


from time import sleep

from API.API_TaoKe.API_TaoKe_Good import TaoKeGoodAnalysisApi
from extra.select_shop_date import select_shop_date
from extra.db_manager import DBManager

from extra.logger_ import logger

if __name__ == "__main__":
    # 参数
    db_config = "rinnai_py"  # NOQA
    shop_name_list = [
        "林内热水器旗舰店",
        "林内官方旗舰店",
    ]  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "tb_tk_淘宝联盟_商品分析_202504"
    site = "淘宝联盟"  # noqa
    # name_suffix = "商品分析"
    level3Dims = [
        # {"全部推广类型": None, },
        {"超级U选/全部活动": "3_2_5"},
        {"超级淘客/全部活动": "3_2_9"},
        {"普通招商/全部活动": "2_1_1"},
        # {"定向计划/全部计划": "1_3_1"},
        # {"营销计划日常": "1_2_1"},
        # {"自选计划": "1_4_1"},
        # {"通用计划": "1_1_1"}
    ]

    # 数据采集
    shop_cookies, crawl_day_list = select_shop_date(table_name, site, shop_name_list, 5)
    # crawl_day_list = get_date_range('2025-05-01', '2025-05-31')

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]
        for level in level3Dims:
            name_suffix, level3_dim = next(iter(level.items()))
            Obj = TaoKeGoodAnalysisApi(
                cookie, name_suffix=name_suffix, level3_dim=level3_dim
            )
            task_status_list_res = (
                Obj.goods_task_status_list()
            )  # 任务状态列表json数据包
            finish_task, un_finish_task = Obj.get_task_status_list(
                task_status_list_res=task_status_list_res
            )  # 解析数据包, 获取任务状态id

            for day in crawl_day_list:
                # 调用create_goods_analysis_task(函数创建,下载任务
                Obj.create_goods_analysis_task(
                    start_time=day, end_time=day, finish_task=finish_task
                )
                # sleep(10)

            date_finish = []  # 已完成的日期列表
            count = 0

            while True:

                if len(date_finish) < len(crawl_day_list):
                    if count > 0:
                        sleep(30)

                    # 计算待采集的日期列表（从需要采集的日期中排除已完成的日期）
                    remaining_days = list(set(crawl_day_list) - set(date_finish))

                    # logger.info(f"待采集{remaining_days}{name_suffix}")
                    for remaining_day in remaining_days:
                        logger.info(
                            f"\n{'=' * 120}\n正在采集{shop_name}，{remaining_day}的数据"
                        )
                        finish_id = Obj.get_finish_id(
                            start_time=remaining_day, end_time=remaining_day
                        )
                        if finish_id:
                            # 获取报表下载链接
                            items = Obj.fetch_goods_file_link(finish_id)

                            for item in items:
                                item.update(
                                    {
                                        "店铺名称": shop_name,
                                        "统计日期": remaining_day,
                                        "计划类型": name_suffix,
                                    }
                                )
                                item["key"] = (
                                    f"{item['商品ID']}_{item['店铺名称']}_{item['计划类型']}_{item['统计日期']}"
                                )

                            DBManager(db_config=db_config).update_insert_data(
                                items, table_name, primary_key="key"
                            )
                            logger.info(f"{shop_name_list},{remaining_day}已入库")
                            date_finish.append(i)
                    count = count + 1

                else:
                    break

        logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")

# python tb_tk_淘宝联盟_商品分析_202504.py --start-date=2025-03-27 --end-date=2025-04-18
