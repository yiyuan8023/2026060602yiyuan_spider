import re
import sys
import os
from pathlib import Path
from typing import List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
print(PROJECT_ROOT)
os.environ["LOG_MODE"] = "both"  # 日志输出到控制台和文件

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from API.API_TaoXi_GuangHe import GuangHeAssetOverviewApi
from database import DBManager

from extra.logger_ import logger
from extra.select_shop_date import select_shop_date

# 最终执行脚本只保留店铺、表名、日期选择和入库编排；接口逻辑放在 API 层。
TASK_CONFIG = {
    "table_name": "tb_光合平台_内容数据_资产总览_商品明细_内容消费_202606",
    "site": "生意参谋",
    "date_type": "day",
    "metric_type": "内容消费",
    "local_excel_path": "",
    "shops": [
        {"shop_name": "林内官方旗舰店", "db_config": "rinnai_py", "recent_period": 3, },
        {"shop_name": "林内热水器旗舰店", "db_config": "rinnai_py", "recent_period": 3, },
    ],
}


def get_day_from_file_name(file_path: str) -> Optional[str]:
    """从光合下载文件名中提取统计日期，供本地样例调试使用。"""
    match = re.search(r"商品分析_(\d{8})", Path(file_path).name)
    if not match:
        return None
    value = match.group(1)
    return f"{value[:4]}-{value[4:6]}-{value[6:8]}"


def build_items(
        items: List[dict],
        shop_name: str,
        day: str,
        date_type: str,
        metric_type: str,
) -> List[dict]:
    """补充店铺、日期、指标类型和唯一 key，生成最终入库数据。"""
    result = []
    for item in items:
        product_id = str(item.get("商品id", "")).strip()
        if not product_id:
            continue

        item.update(
            {
                "店铺名称": shop_name,
                "统计日期": day,
                "日期类型": date_type,
                "指标类型": metric_type,
            }
        )
        item["key"] = f"{day}_{product_id}_{metric_type}_{date_type}_{shop_name}"
        result.append(item)
    return result


if __name__ == "__main__":
    table_name = TASK_CONFIG["table_name"]
    site = TASK_CONFIG["site"]
    date_type = TASK_CONFIG["date_type"]
    metric_type = TASK_CONFIG["metric_type"]
    local_excel_path = TASK_CONFIG["local_excel_path"]

    # LOCAL_EXCEL_PATH 仅用于本地样例验证；正式采集保持为空，走在线下载。
    local_excel_day = get_day_from_file_name(local_excel_path) if local_excel_path else None

    for shop_config in TASK_CONFIG["shops"]:
        shop_name = shop_config["shop_name"]
        db_config = shop_config["db_config"]
        recent_period = shop_config["recent_period"]

        # select_shop_date 返回店铺 Cookie 和待采集日期，Cookie 字符串使用 shop_cookie[1]。
        shop_cookies, crawl_day_list = select_shop_date(
            table_name,
            site,
            [shop_name],
            recent_period,
        )

        if local_excel_path and local_excel_day:
            crawl_day_list = [local_excel_day]

        for shop_cookie in shop_cookies:
            shop_name = shop_cookie[0]
            cookie = shop_cookie[1]
            api = GuangHeAssetOverviewApi(cookie)

            for day in crawl_day_list:
                logger.info(f"正在采集【{shop_name}】{day} 光合平台商品明细内容消费数据")

                if local_excel_path:
                    items = api.read_local_excel(local_excel_path)
                else:
                    items = api.product_analysis_content_consumption_excel(day)

                if not items:
                    logger.warning(
                        f"{shop_name},{day} 光合平台商品明细内容消费数据为空，跳过入库"
                    )
                    continue

                # 统一在执行层补业务维度，API 层只返回平台原始明细。
                items = build_items(items, shop_name, day, date_type, metric_type)
                if not items:
                    logger.warning(
                        f"{shop_name},{day} 光合平台商品明细内容消费数据缺少商品id，跳过入库"
                    )
                    continue

                with DBManager(db_config) as db_manager:
                    db_manager.update_insert_data(items, table_name, primary_key="key")

                logger.info(f"{shop_name},{day} 的光合平台商品明细内容消费数据已入库")
                logger.info("-" * 100)

    logger.info(f"\n{'*' * 120}")
