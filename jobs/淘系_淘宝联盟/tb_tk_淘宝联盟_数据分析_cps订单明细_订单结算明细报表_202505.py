"""
开发说明：
- 作者：一元
- 创建时间：2026-06-06 13:28:51
- 最近修改：2026-06-08 16:30:08
- 文件用途：采集淘宝联盟 CPS 订单结算明细报表，按店铺和日期区间创建下载任务后写入目标表。
- 业务范围：适用于淘宝联盟数据分析中的 CPS 订单明细，平台限制通常为最近 365 天且单次最多 31 天。
- 依赖入口：调用 API.API_TaoKe.API_TaoKe_Cps.TaoKeCpsApi 创建和下载 CPS 报表，使用 select_shop_date 获取店铺 Cookie 和日期，使用 date_utils 拆分日期区间，使用 DBManager 入库，日志走 extra.logger_。
- 验收方式：修改后执行 py_compile；涉及接口或入库逻辑时先单店铺、小日期范围验证任务状态、下载字段、主键和目标表写入。
- 注意事项：正式运行建议通过 run_job.py 设置项目根路径和 LOG_MODE；不得输出真实 Cookie、签名下载 URL 或数据库敏感配置。
"""

from time import sleep
from typing import List

from API.API_TaoKe.API_TaoKe_Cps import TaoKeCpsApi
from database import DBManager
from date_utils import get_date_min_max, get_split_date_range
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date


# 最终任务脚本只保留店铺、表名、日期选择、报表名称和入库编排；接口逻辑放在 API 层。
TASK_CONFIG = {
    "table_name": "tb_tk_淘宝联盟_数据分析_cps订单明细_订单结算明细报表_202505",
    "site": "淘宝联盟",
    "name_suffix": "订单结算明细报表",
    "shops": [
        {"shop_name": "林内热水器旗舰店", "db_config": "rinnai_py", "recent_days": 10, },  # noqa
        {"shop_name": "林内官方旗舰店", "db_config": "rinnai_py", "recent_days": 10, },  # noqa
    ],
}


def build_items(items: List[dict], shop_name: str) -> List[dict]:
    """补充店铺名称，生成最终入库数据。"""
    for item in items:
        item["店铺名称"] = shop_name
    return items


if __name__ == "__main__":
    table_name = TASK_CONFIG["table_name"]
    site = TASK_CONFIG["site"]
    name_suffix = TASK_CONFIG["name_suffix"]

    for shop_config in TASK_CONFIG["shops"]:
        target_shop_name = shop_config["shop_name"]
        db_config = shop_config["db_config"]
        recent_days = shop_config["recent_days"]

        shop_cookies, crawl_day_list = select_shop_date(
            table_name,
            site,
            [target_shop_name],
            recent_days,
        )
        min_date, max_date = get_date_min_max(crawl_day_list)
        split_date_list = get_split_date_range(min_date, max_date)

        for shop_cookie in shop_cookies:
            cookie = shop_cookie[1]
            shop_name = shop_cookie[0]

            for start_time, end_time in split_date_list:
                api = TaoKeCpsApi(cookie, start_time, end_time, name_suffix=name_suffix)
                api.tb_tk_cps_settlement_report()

                task_status_list_res = api.cps_task_status_list()
                finish_task, un_finish_task = api.get_task_status_list(
                    task_status_list_res=task_status_list_res
                )

                while un_finish_task:
                    logger.info(f"{shop_name},{start_time}_{end_time} CPS 报表任务未完成，等待 100s")
                    sleep(100)

                    task_status_list_res = api.cps_task_status_list()
                    finish_task, un_finish_task = api.get_task_status_list(
                        task_status_list_res=task_status_list_res
                    )
                    logger.info(un_finish_task)

                logger.info(
                    f"\n{'=' * 120}\n开始采集【{shop_name}】{start_time}_{end_time} CPS 订单结算明细数据"
                )
                report_name = f"{start_time} 00:00:00~{end_time} 23:59:59-{name_suffix}"
                report_id = finish_task.get(report_name)
                if not report_id:
                    logger.warning(f"{shop_name},{start_time}_{end_time} 未找到报表任务，跳过入库")
                    continue

                sleep(5)
                items = api.fetch_cps_file_link(report_id)
                if not items:
                    logger.warning(f"{shop_name},{start_time}_{end_time} CPS 订单结算明细数据为空，跳过入库")
                    continue

                items = build_items(items, shop_name)
                with DBManager(db_config=db_config) as db_manager:
                    db_manager.update_insert_data(
                        items,
                        table_name,
                        primary_key="淘宝子订单编号",
                    )

                logger.info(f"{shop_name},{start_time}_{end_time} CPS 订单结算明细数据已入库")

            logger.info(f"\n{'-' * 100}")

    logger.info(f"\n{'*' * 120}")
