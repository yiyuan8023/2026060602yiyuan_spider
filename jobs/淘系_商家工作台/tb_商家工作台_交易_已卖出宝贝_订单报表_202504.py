"""
开发说明：
- 作者：一元
- 创建时间：2026-06-12 17:14:38
- 最近修改：2026-06-12 17:20:25
- 文件用途：执行商家工作台交易已卖出宝贝订单报表采集任务，负责组织店铺、日期、目标表、店铺级并发、店铺字段补充和入库流程。
- 业务范围：适用于淘系商家工作台交易已卖出宝贝订单报表，当前默认采集脚本内配置店铺的近期数据。
- 依赖入口：使用 API.API_TaoXi_GongZuoTai.TaoXiGongZuoTaiOrderReportApi、extra.select_shop_date、database.DBManager、date_utils.get_min_max_timestamps 和 extra.logger_。
- 验收方式：修改后执行 py_compile；真实请求时用单店铺、单日期验证报表下载、解析行数、目标表和主键。
- 注意事项：订单报表脚本独立于宝贝销售明细报表脚本；不在脚本内记录真实 Cookie、数据库密码或签名下载 URL；未确认前不做大范围真实写库。
"""

from concurrent.futures import ThreadPoolExecutor, as_completed

from API.API_TaoXi_GongZuoTai import TaoXiGongZuoTaiOrderReportApi
from database import DBManager
from date_utils import get_min_max_timestamps
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date


TABLE_NAME = "tb_商家工作台_交易_已卖出宝贝_订单报表_202504"
SITE = "生意参谋"
PRIMARY_KEY = "订单编号"
MAX_WORKERS = 3

SHOP_CONFIGS = [
    {"shop_name": "林内官方旗舰店", "db_config": None, "recent_days": 3},
]


def fetch_shop_report(shop_cookie, shop_config_by_name, start_timestamp, end_timestamp):
    """单店铺订单报表导出和下载，供店铺级并发调用。"""
    shop_name = shop_cookie[0]
    cookie = shop_cookie[1]
    db_config = shop_config_by_name.get(shop_name, {}).get("db_config")
    api = TaoXiGongZuoTaiOrderReportApi(cookie)
    items = api.list_export_order_report(start_timestamp, end_timestamp)
    for item in items:
        item["店铺名称"] = shop_name
    return {"shop_name": shop_name, "db_config": db_config, "items": items}


def write_shop_items(shop_result):
    """主线程写入单店铺结果，避免在线程之间共享数据库连接。"""
    shop_name = shop_result["shop_name"]
    items = shop_result["items"]
    if not items:
        logger.warning(f"{shop_name} 商家工作台订单报表无可写入数据")
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
    start_timestamp, end_timestamp = get_min_max_timestamps(crawl_day_list)

    if not shop_cookies:
        logger.warning("商家工作台订单报表没有可执行店铺")
    else:
        worker_count = min(MAX_WORKERS, len(shop_cookies))
        logger.info(f"商家工作台订单报表店铺级并发开始，店铺数={len(shop_cookies)}，并发数={worker_count}")
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_by_shop = {
                executor.submit(
                    fetch_shop_report,
                    shop_cookie,
                    shop_config_by_name,
                    start_timestamp,
                    end_timestamp,
                ): shop_cookie[0]
                for shop_cookie in shop_cookies
            }
            for future in as_completed(future_by_shop):
                shop_name = future_by_shop[future]
                try:
                    write_shop_items(future.result())
                except Exception:
                    logger.exception(f"{shop_name} 商家工作台订单报表并发采集失败")
                    raise
    logger.info("*" * 100)
