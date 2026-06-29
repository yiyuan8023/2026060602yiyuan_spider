# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-23 19:05:00
- 最近修改：2026-06-23 19:05:00
- 文件用途：执行商家工作台国家补贴审计工作台订单导出采集任务，负责店铺 Cookie、导出参数、Excel 下载解析和默认测试库入库。
- 业务范围：适用于“国家补贴-审计管理-订单导出”，当前默认店铺为林内官方旗舰店和林内热水器旗舰店。
- 依赖入口：调用 TaoXiGongZuoTaiGovSubsidyAuditApi、select_shop_date 和 DBManager。
- 验收方式：执行 py_compile；用 USE_LATEST_SUCCESS_EXPORT=1 下载最近成功导出记录并写入测试库。
- 注意事项：默认会创建新的平台导出任务；需要复用最近成功导出记录时设置环境变量 USE_LATEST_SUCCESS_EXPORT=1；入库字段类型或长度异常时只记录错误，不在脚本内自动修改表结构。
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from API.API_TaoXi_GongZuoTai import TaoXiGongZuoTaiGovSubsidyAuditApi
from database import DBManager
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date


# TABLE_NAME = "tb_商家工作台_国家补贴_审计工作台_订单导出_202606"
TABLE_NAME = "rinnai_tb_政府补贴_审计管理_审计明细_202606" # noqa
SITE = "生意参谋"
PRIMARY_KEY = "交易子订单号"
MAX_WORKERS = 3
USE_LATEST_SUCCESS_EXPORT = os.environ.get("USE_LATEST_SUCCESS_EXPORT") == "1"
AUDIT_YEAR = "2026"
AUDIT_AREA_ID_BY_YEAR = {
    "2024": 429,
    "2025": 428,
    "2026": 427,
    # "2027": 426,
}
EMPTY_DATE_VALUES = {"", "无", "--", "-"}
DATE_COLUMNS = {
    "支付时间",
    "签收时间",
    "开票日期",
    "ocr解析开票日期",
    "确收时间",
}

# 跨店铺通用筛选条件；sellerId 由 SHOP_CONFIGS 按店铺生成，
# auditAreaId 跟年份强绑定；pageSize 只是查总数的占位值，创建导出任务前会用接口 total 覆盖。
BASE_AUDIT_PARAMS = {
    "area": "0",
    "auditAreaId": AUDIT_AREA_ID_BY_YEAR[AUDIT_YEAR],
    "auditCategory": "0",
    "auditTemplateId": 68,
    "city": "0",
    "exception": False,
    "pageIndex": 1,
    "pageSize": 1,
    "pro": "0",
    "source": "seller",
    "year": AUDIT_YEAR,
    "ztSeller": False,
}


def build_audit_params(seller_id, audit_year=AUDIT_YEAR):
    """按店铺 sellerId 生成国家补贴审计订单导出筛选条件。"""
    audit_year = str(audit_year)
    if audit_year not in AUDIT_AREA_ID_BY_YEAR:
        raise ValueError(f"未配置国家补贴审计年份对应的 auditAreaId: {audit_year}")

    audit_params = dict(BASE_AUDIT_PARAMS)
    audit_params["auditAreaId"] = AUDIT_AREA_ID_BY_YEAR[audit_year]
    audit_params["year"] = audit_year
    audit_params["sellerId"] = seller_id
    return audit_params


SHOP_CONFIGS = [
    {
        "shop_name": "林内官方旗舰店",
        "db_config": "rinnai",
        "recent_days": 1,
        "audit_params": build_audit_params(1087143051),
    },
    {
        "shop_name": "林内热水器旗舰店",
        "db_config": "rinnai",
        "recent_days": 1,
        "audit_params": build_audit_params(2208107135654),
    },
    {
        "shop_name": "林内品牌折扣店",
        "db_config": "rinnai",
        "recent_days": 1,
        "audit_params": build_audit_params(3830928885),
    },
    {
        "shop_name": "林内厨电旗舰店",
        "db_config": "rinnai",
        "recent_days": 1,
        "audit_params": build_audit_params(2212375622312),
    },
]


def fetch_shop_report(shop_cookie, shop_config_by_name):
    """单店铺国家补贴审计订单导出下载。"""
    shop_name = shop_cookie[0]
    cookie = shop_cookie[1]
    shop_config = shop_config_by_name.get(shop_name, {})
    audit_params = dict(shop_config.get("audit_params") or BASE_AUDIT_PARAMS)

    api = TaoXiGongZuoTaiGovSubsidyAuditApi(cookie)
    if USE_LATEST_SUCCESS_EXPORT:
        items = api.download_latest_success_audit_order_export(audit_params)
    else:
        items = api.export_audit_order_records(audit_params)

    for item in items:
        normalize_date_fields(item)
        item["店铺名称"] = shop_name
    return {
        "shop_name": shop_name,
        "db_config": shop_config.get("db_config"),
        "items": items,
    }


def normalize_date_fields(item):
    """平台导出用“无”占位日期空值，入库前转为空。"""
    for column in DATE_COLUMNS:
        if item.get(column) in EMPTY_DATE_VALUES:
            item[column] = ""


def write_shop_items(shop_result):
    """写入单店铺采集结果。"""
    shop_name = shop_result["shop_name"]
    items = shop_result["items"]
    if not items:
        logger.warning(f"{shop_name} 国家补贴审计工作台订单导出无可写入数据")
        return

    with DBManager(db_config=shop_result["db_config"]) as db_manager:
        db_manager.update_insert_data(items, TABLE_NAME, primary_key=PRIMARY_KEY)
    logger.info("-" * 100)


if __name__ == "__main__":
    shop_name_list = [shop_config["shop_name"] for shop_config in SHOP_CONFIGS]
    shop_config_by_name = {shop_config["shop_name"]: shop_config for shop_config in SHOP_CONFIGS}
    recent_days = max(shop_config["recent_days"] for shop_config in SHOP_CONFIGS)
    shop_cookies, _crawl_day_list = select_shop_date(
        TABLE_NAME,
        SITE,
        shop_name_list,
        recent_days,
    )

    if not shop_cookies:
        logger.warning("国家补贴审计工作台订单导出没有可执行店铺")
    else:
        worker_count = min(MAX_WORKERS, len(shop_cookies))
        logger.info(
            f"国家补贴审计工作台订单导出店铺级并发开始，"
            f"店铺数={len(shop_cookies)}，并发数={worker_count}"
        )
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_by_shop = {
                executor.submit(
                    fetch_shop_report,
                    shop_cookie,
                    shop_config_by_name,
                ): shop_cookie[0]
                for shop_cookie in shop_cookies
            }
            for future in as_completed(future_by_shop):
                shop_name = future_by_shop[future]
                try:
                    write_shop_items(future.result())
                except Exception:
                    logger.exception(f"{shop_name} 国家补贴审计工作台订单导出并发采集失败")
                    raise
    logger.info("*" * 100)
