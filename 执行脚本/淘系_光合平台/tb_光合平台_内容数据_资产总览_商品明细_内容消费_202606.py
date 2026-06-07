import re
from pathlib import Path
from typing import List, Optional

from API.API_TX_GuangHe import GuangHeAssetOverviewApi
from extra.db_manager import DBManager
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date


# 最终执行脚本只保留店铺、表名、日期选择和入库编排；接口逻辑放在 API 层。
SHOP_NAME_LIST = [
    "林内官方旗舰店",
]
TABLE_NAME = "tb_光合平台_内容数据_资产总览_商品明细_内容消费_202606"
SITE = "生意参谋"
DATE_TYPE = "day"
METRIC_TYPE = "内容消费"
LOCAL_EXCEL_PATH = ""


def get_day_from_file_name(file_path: str) -> Optional[str]:
    """从光合下载文件名中提取统计日期，供本地样例调试使用。"""
    match = re.search(r"商品分析_(\d{8})", Path(file_path).name)
    if not match:
        return None
    value = match.group(1)
    return f"{value[:4]}-{value[4:6]}-{value[6:8]}"


def build_items(items: List[dict], shop_name: str, day: str) -> List[dict]:
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
                "日期类型": DATE_TYPE,
                "指标类型": METRIC_TYPE,
            }
        )
        item["key"] = f"{day}_{product_id}_{METRIC_TYPE}_{DATE_TYPE}_{shop_name}"
        result.append(item)
    return result


if __name__ == "__main__":
    # select_shop_date 返回店铺 Cookie 和待采集日期，Cookie 字符串使用 shop_cookie[1]。
    shop_cookies, crawl_day_list = select_shop_date(TABLE_NAME, SITE, SHOP_NAME_LIST, 1)

    # LOCAL_EXCEL_PATH 仅用于本地样例验证；正式采集保持为空，走在线下载。
    local_excel_day = get_day_from_file_name(LOCAL_EXCEL_PATH) if LOCAL_EXCEL_PATH else None
    if LOCAL_EXCEL_PATH and local_excel_day:
        crawl_day_list = [local_excel_day]

    for shop_cookie in shop_cookies:
        shop_name = shop_cookie[0]
        cookie = shop_cookie[1]
        api = GuangHeAssetOverviewApi(cookie)

        for day in crawl_day_list:
            logger.info(f"正在采集【{shop_name}】{day} 光合平台商品明细内容消费数据")

            if LOCAL_EXCEL_PATH:
                items = api.read_local_excel(LOCAL_EXCEL_PATH)
            else:
                items = api.product_analysis_content_consumption_excel(day)

            # 统一在执行层补业务维度，API 层只返回平台原始明细。
            items = build_items(items or [], shop_name, day)
            DBManager().update_insert_data(items, TABLE_NAME, primary_key="key")

            logger.info(f"{shop_name},{day} 的光合平台商品明细内容消费数据已入库")
            logger.info("-" * 100)

    logger.info(f"\n{'*' * 120}")
