"""
开发说明：
- 作者：一元
- 创建时间：2026-06-06 13:28:51
- 最近修改：2026-06-08 16:56:21
- 文件用途：采集淘宝联盟定向计划报表分天明细，补充店铺和唯一 key 后写入目标表。
- 业务范围：适用于淘宝联盟数据分析中的定向计划报表，按店铺和采集日期范围拉取分天明细。
- 依赖入口：调用 API.API_TaoKe.API_Taoke_DingXiang.TaoKeDingXiangApi 获取定向计划数据，使用 select_shop_date 获取店铺 Cookie 和日期，使用 DBManager 入库，日志走 extra.logger_。
- 验收方式：修改后执行 py_compile；涉及接口或入库逻辑时先单店铺、小日期范围验证字段、唯一 key 和目标表写入。
- 注意事项：正式运行建议通过 run_job.py 设置项目根路径和 LOG_MODE；不得输出真实 Cookie、签名下载 URL 或数据库敏感配置。
"""

from typing import List

from API.API_TaoKe.API_Taoke_DingXiang import TaoKeDingXiangApi
from database import DBManager
from date_utils import get_date_min_max
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date


# 最终任务脚本只保留店铺、表名、日期选择和入库编排；接口逻辑放在 API 层。
TASK_CONFIG = {
    "table_name": "tb_tk_淘宝联盟_数据分析_定向计划报表_分天明细_202509",
    "site": "淘宝联盟",
    "shops": [
        {"shop_name": "林内热水器旗舰店", "db_config": "rinnai_py", "recent_days": 30, },  # noqa
        {"shop_name": "林内官方旗舰店", "db_config": "rinnai_py", "recent_days": 30, },  # noqa
    ],
}


def build_items(raw_items: List[dict], item_shop_name: str) -> List[dict]:
    """补充店铺名称和唯一 key，生成最终入库数据。"""
    result = []
    for item in raw_items:
        task_id = str(item.get("任务id", "")).strip()
        stat_day = str(item.get("统计日期", "")).strip()
        if not task_id or not stat_day:
            continue

        item["店铺名称"] = item_shop_name
        item["key"] = f"{item_shop_name}_{task_id}_{stat_day}"
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
        min_time, max_time = get_date_min_max(crawl_day_list)

        for shop_cookie in shop_cookies:
            cookie = shop_cookie[1]
            shop_name = shop_cookie[0]
            api = TaoKeDingXiangApi(cookie)

            logger.info(f"正在采集【{shop_name}】{min_time}_{max_time} 淘宝联盟定向计划分天明细数据")
            items = api.get_campaign(min_time, max_time)
            if not items:
                logger.warning(f"{shop_name},{min_time}_{max_time} 定向计划分天明细数据为空，跳过入库")
                continue

            items = build_items(items, shop_name)
            if not items:
                logger.warning(f"{shop_name},{min_time}_{max_time} 定向计划分天明细缺少任务id或统计日期，跳过入库")
                continue

            with DBManager(db_config=db_config) as db_manager:
                db_manager.update_insert_data(items, table_name, primary_key="key")

            logger.info(f"{shop_name},{crawl_day_list} 定向计划分天明细数据已入库")
            logger.info(f"\n{'-' * 100}")

    logger.info(f"\n{'*' * 120}")
