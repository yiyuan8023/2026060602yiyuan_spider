# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-12 18:21:46
- 最近修改：2026-06-12 18:21:46
- 文件用途：执行千牛商家工作台价保管理订单赔付详情采集任务，负责组织店铺、日期、目标表、分页采集、字段解析和入库流程。
- 业务范围：适用于 https://qn.taobao.com/home.htm/price-center-manager 的价保记录查询，默认采集脚本内配置店铺的近期申请记录。
- 依赖入口：使用 API.API_TaoXi_GongZuoTai.TaoXiGongZuoTaiPriceProtectionApi、build_price_protection_records、extra.select_shop_date、database.DBManager、date_utils.get_date_min_max 和 extra.logger_。
- 验收方式：修改后执行 py_compile；真实请求时用单店铺、单日期验证接口分页、解析行数、目标表和主键。
- 注意事项：不在脚本内记录真实 Cookie、数据库密码或签名 URL；未确认前不做大范围真实写库。
"""

from concurrent.futures import ThreadPoolExecutor, as_completed

from API.API_TaoXi_GongZuoTai import TaoXiGongZuoTaiPriceProtectionApi
from database import DBManager
from date_utils import get_date_min_max
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date


TABLE_NAME = "tb_商家工作台_价保中心_价保管理_价保订单赔付详情_202606"
SITE = "生意参谋"
PRIMARY_KEY = "价保申请ID"
MAX_WORKERS = 3
PAGE_SIZE = 100
TAB_ALL_STATUS = 4

SHOP_CONFIGS = [
    # {"shop_name": "林内官方旗舰店", "db_config": None, "recent_days": 3},
    {"shop_name": "林内热水器旗舰店", "db_config": None, "recent_days": 30},
]


def build_apply_time_range(crawl_day_list):
    """把 select_shop_date 的日期列表转为价保接口申请时间范围。"""
    min_date, max_date = get_date_min_max(crawl_day_list)
    return f"{min_date} 00:00:00", f"{max_date} 23:59:59"


def fetch_shop_records(shop_cookie, shop_config_by_name, apply_min_time, apply_max_time):
    """单店铺导出价保订单赔付详情，供店铺级并发调用。"""
    shop_name = shop_cookie[0]
    cookie = shop_cookie[1]
    extra_cookie = shop_cookie[2] if len(shop_cookie) > 2 else None
    db_config = shop_config_by_name.get(shop_name, {}).get("db_config")
    api = TaoXiGongZuoTaiPriceProtectionApi(
        cookie,
        shop_name=shop_name,
        extra_cookie=extra_cookie,
    )
    items = api.download_export_price_protection_records(
        tab=TAB_ALL_STATUS,
        apply_min_time=apply_min_time,
        apply_max_time=apply_max_time,
    )
    for item in items:
        item["店铺名称"] = shop_name
        item["查询开始时间"] = apply_min_time
        item["查询结束时间"] = apply_max_time
    return {"shop_name": shop_name, "db_config": db_config, "items": items}


def write_shop_items(shop_result):
    """主线程写入单店铺结果，避免在线程之间共享数据库连接。"""
    shop_name = shop_result["shop_name"]
    items = shop_result["items"]
    if not items:
        logger.warning(f"{shop_name} 千牛价保订单赔付详情无可写入数据")
        return

    with DBManager(db_config=shop_result["db_config"]) as db_manager:
        db_manager.update_insert_data(items, TABLE_NAME, primary_key=PRIMARY_KEY)
    logger.info("-" * 100)


if __name__ == "__main__":
    shop_name_list = [shop_config["shop_name"] for shop_config in SHOP_CONFIGS]
    shop_config_by_name = {shop_config["shop_name"]: shop_config for shop_config in SHOP_CONFIGS}
    recent_days = max(shop_config["recent_days"] for shop_config in SHOP_CONFIGS)
    shop_cookies, crawl_day_list = select_shop_date(
        TABLE_NAME,
        SITE,
        shop_name_list,
        recent_days,
    )
    apply_min_time, apply_max_time = build_apply_time_range(crawl_day_list)

    if not shop_cookies:
        logger.warning("千牛价保订单赔付详情没有可执行店铺")
    else:
        worker_count = min(MAX_WORKERS, len(shop_cookies))
        logger.info(
            f"千牛价保订单赔付详情店铺级并发开始，店铺数={len(shop_cookies)}，"
            f"并发数={worker_count}，申请时间={apply_min_time}~{apply_max_time}"
        )
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_by_shop = {
                executor.submit(
                    fetch_shop_records,
                    shop_cookie,
                    shop_config_by_name,
                    apply_min_time,
                    apply_max_time,
                ): shop_cookie[0]
                for shop_cookie in shop_cookies
            }
            for future in as_completed(future_by_shop):
                shop_name = future_by_shop[future]
                try:
                    write_shop_items(future.result())
                except Exception:
                    logger.exception(f"{shop_name} 千牛价保订单赔付详情并发采集失败")
                    raise
    logger.info("*" * 100)
