"""
开发说明：
- 作者：一元
- 创建时间：2026-06-06 13:28:51
- 最近修改：2026-06-08 16:56:21
- 文件用途：采集淘宝联盟商品分析数据，按店铺、日期和计划类型创建并下载报表后写入目标表。
- 业务范围：适用于淘宝联盟商品分析页面，覆盖超级 U 选、超级淘客、普通招商、营销计划、自选计划和通用计划等计划类型。
- 依赖入口：调用 API.API_TaoKe.API_TaoKe_Good.TaoKeGoodAnalysisApi 创建和下载报表，使用 select_shop_date 获取店铺 Cookie 和日期，使用 DBManager 入库，日志走 extra.logger_。
- 验收方式：修改后执行 py_compile；涉及接口或入库逻辑时先单店铺、单日期、单计划类型验证任务创建、下载字段、唯一 key 和目标表写入。
- 注意事项：正式运行建议通过 run_job.py 设置项目根路径和 LOG_MODE；不得输出真实 Cookie、签名下载 URL 或数据库敏感配置。
"""

from time import sleep
from typing import List

from API.API_TaoKe.API_TaoKe_Good import TaoKeGoodAnalysisApi
from database import DBManager
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date

# 最终任务脚本只保留店铺、表名、日期选择、计划类型和入库编排；接口逻辑放在 API 层。
TASK_CONFIG = {
    "table_name": "tb_tk_淘宝联盟_商品分析_202504",
    "site": "淘宝联盟",
    "shops": [
        {"shop_name": "林内热水器旗舰店", "db_config": "rinnai_py", "recent_days": 5, },  # noqa
        {"shop_name": "林内官方旗舰店", "db_config": "rinnai_py", "recent_days": 5, },  # noqa
    ],
    "level3_dims": [
        # {"name": "全部推广类型", "value": None},# 不要
        {"name": "超级U选/全部活动", "value": "3_2_5"},
        {"name": "超级淘客/全部活动", "value": "3_2_9"},
        {"name": "普通招商/全部活动", "value": "2_1_1"},
        # {"name": "定向计划/全部计划", "value": "1_3_1"}, # 不要
        {"name": "营销计划日常", "value": "1_2_1"},
        {"name": "自选计划", "value": "1_4_1"},
        {"name": "通用计划", "value": "1_1_1"},
    ],
}


def build_items(
        raw_items: List[dict],
        item_shop_name: str,
        stat_day: str,
        item_plan_type: str,
) -> List[dict]:
    """补充店铺、统计日期、计划类型和唯一 key，生成最终入库数据。"""
    result = []
    for item in raw_items:
        product_id = str(item.get("商品ID", "")).strip()
        if not product_id:
            continue

        item.update(
            {
                "店铺名称": item_shop_name,
                "统计日期": stat_day,
                "计划类型": item_plan_type,
            }
        )
        item["key"] = f"{product_id}_{item_shop_name}_{item_plan_type}_{stat_day}"
        result.append(item)
    return result


if __name__ == "__main__":
    table_name = TASK_CONFIG["table_name"]
    site = TASK_CONFIG["site"]

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

        for shop_cookie in shop_cookies:
            cookie = shop_cookie[1]
            shop_name = shop_cookie[0]

            for level_config in TASK_CONFIG["level3_dims"]:
                plan_type = level_config["name"]
                level3_dim = level_config["value"]
                api = TaoKeGoodAnalysisApi(cookie, name_suffix=plan_type, level3_dim=level3_dim, )

                task_status_list_res = api.goods_task_status_list()
                finish_task, _un_finish_task = api.get_task_status_list(
                    task_status_list_res=task_status_list_res
                )

                for day in crawl_day_list:
                    api.create_goods_analysis_task(start_time=day, end_time=day, finish_task=finish_task, )

                finished_days = set()
                poll_count = 0

                while len(finished_days) < len(crawl_day_list):
                    if poll_count > 0:
                        sleep(30)

                    remaining_days = [
                        day for day in crawl_day_list if day not in finished_days
                    ]
                    for day in remaining_days:
                        logger.info(
                            f"\n{'=' * 120}\n正在采集【{shop_name}】{day} 淘宝联盟商品分析 {plan_type} 数据"
                        )
                        finish_id = api.get_finish_id(start_time=day, end_time=day)
                        if not finish_id:
                            logger.warning(f"{shop_name},{day},{plan_type} 报表任务未完成，继续等待")
                            continue

                        items = api.fetch_goods_file_link(finish_id)
                        if not items:
                            logger.warning(f"{shop_name},{day},{plan_type} 商品分析数据为空，跳过入库")
                            finished_days.add(day)
                            continue

                        items = build_items(items, shop_name, day, plan_type)
                        if not items:
                            logger.warning(f"{shop_name},{day},{plan_type} 商品分析数据缺少商品ID，跳过入库")
                            finished_days.add(day)
                            continue

                        with DBManager(db_config=db_config) as db_manager:
                            db_manager.update_insert_data(items, table_name, primary_key="key")

                        logger.info(f"{shop_name},{day},{plan_type} 商品分析数据已入库")
                        finished_days.add(day)

                    poll_count += 1

            logger.info(f"\n{'-' * 100}")

    logger.info(f"\n{'*' * 120}")
