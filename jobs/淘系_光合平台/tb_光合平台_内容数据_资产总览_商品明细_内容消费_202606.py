"""
开发说明：
- 作者：一元
- 创建时间：2026-06-06 22:47:55
- 最近修改：2026-06-08 16:56:21
- 文件用途：采集光合平台资产总览中商品明细的内容消费数据，补充业务维度后写入目标表。
- 业务范围：适用于淘系光合平台内容数据，按店铺和统计日期采集商品明细内容消费指标。
- 依赖入口：调用 API.API_TaoXi_GuangHe.GuangHeAssetOverviewApi 获取和解析数据，使用 select_shop_date 获取店铺 Cookie 和采集日期，使用 DBManager 入库，日志走 extra.logger_。
- 验收方式：修改后执行 py_compile；涉及接口或入库逻辑时先单店铺、单日期验证下载结果、字段补充、唯一 key 和目标表写入。
- 注意事项：正式运行建议通过 run_job.py 设置项目根路径和 LOG_MODE；不得输出真实 Cookie、签名下载 URL 或数据库敏感配置。
"""

from typing import List
from API.API_TaoXi_GuangHe import GuangHeAssetOverviewApi
from database import DBManager
from date_utils import get_date_range
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date

# 最终任务脚本只保留店铺、表名、日期选择和入库编排；接口逻辑放在 API 层。
TASK_CONFIG = {
    "table_name": "tb_光合平台_内容数据_资产总览_商品明细_内容消费_202606",
    "site": "生意参谋",
    "date_type": "day",
    "metric_type": "内容消费",
    "shops": [
        {"shop_name": "林内官方旗舰店", "db_config": "rinnai_py", "recent_days": 3, },  # noqa
        {"shop_name": "林内热水器旗舰店", "db_config": "rinnai_py", "recent_days": 3, },  # noqa
    ],
}


def build_items(
        raw_items: List[dict],
        item_shop_name: str,
        stat_day: str,
        item_date_type: str,
        item_metric_type: str,
) -> List[dict]:
    """补充店铺、日期、指标类型和唯一 key，生成最终入库数据。"""
    result = []
    for item in raw_items:
        product_id = str(item.get("商品id", "")).strip()
        if not product_id:
            continue

        item.update(
            {
                "店铺名称": item_shop_name,
                "统计日期": stat_day,
                "日期类型": item_date_type,
                "指标类型": item_metric_type,
            }
        )
        item["key"] = f"{stat_day}_{product_id}_{item_metric_type}_{item_date_type}_{item_shop_name}"
        result.append(item)
    return result


if __name__ == "__main__":
    table_name = TASK_CONFIG["table_name"]
    site = TASK_CONFIG["site"]
    date_type = TASK_CONFIG["date_type"]
    metric_type = TASK_CONFIG["metric_type"]

    for shop_config in TASK_CONFIG["shops"]:
        shop_name = shop_config["shop_name"]
        db_config = shop_config["db_config"]
        recent_days = shop_config["recent_days"]

        # select_shop_date 返回店铺 Cookie 和待采集日期，Cookie 字符串使用 shop_cookie[1]。
        shop_cookies, crawl_day_list = select_shop_date(table_name, site, [shop_name], recent_days, )

        # crawl_day_list = get_date_range('2026-03-01', '2026-06-07')

        for shop_cookie in shop_cookies:
            shop_name = shop_cookie[0]
            cookie = shop_cookie[1]
            api = GuangHeAssetOverviewApi(cookie)

            for day in crawl_day_list:
                logger.info(f"正在采集【{shop_name}】{day} 光合平台商品明细内容消费数据")

                items = api.product_analysis_content_consumption_excel(day)

                if not items:
                    logger.warning(f"{shop_name},{day} 光合平台商品明细内容消费数据为空，跳过入库")
                    continue

                # 统一在执行层补业务维度，API 层只返回平台原始明细。
                items = build_items(items, shop_name, day, date_type, metric_type)
                if not items:
                    logger.warning(f"{shop_name},{day} 光合平台商品明细内容消费数据缺少商品id，跳过入库")
                    continue

                with DBManager(db_config) as db_manager:
                    db_manager.update_insert_data(items, table_name, primary_key="key")

                logger.info(f"{shop_name},{day} 的光合平台商品明细内容消费数据已入库")
                logger.info(f"\n{'-' * 100}")

    logger.info(f"\n{'*' * 120}")
