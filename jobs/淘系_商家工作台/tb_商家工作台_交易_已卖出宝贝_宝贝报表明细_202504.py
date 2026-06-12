"""
开发说明：
- 作者：一元
- 创建时间：2026-06-06 13:28:51
- 最近修改：2026-06-10 21:36:12
- 文件用途：执行商家工作台交易已卖出宝贝报表明细采集任务，负责组织店铺、日期、目标表、店铺字段补充和入库流程。
- 业务范围：适用于淘系商家工作台交易已卖出宝贝报表明细，当前默认采集脚本内配置店铺的近期数据。
- 依赖入口：使用 API.API_TaoXi_GongZuoTai.TaoXiGongZuoTaiTradeApi、extra.select_shop_date、database.DBManager、date_utils.get_min_max_timestamps 和 extra.logger_。
- 验收方式：修改后执行 py_compile；真实请求时用单店铺、单日期验证报表下载、解析行数、目标表和主键。
- 注意事项：不在脚本内记录真实 Cookie、数据库密码或签名下载 URL；未确认前不做大范围真实写库。
"""

from API.API_TaoXi_GongZuoTai import TaoXiGongZuoTaiTradeApi
from database import DBManager
from date_utils import get_min_max_timestamps
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date


TABLE_NAME = "tb_商家工作台_交易_已卖出宝贝_宝贝报表明细_202504"
SITE = "生意参谋"
PRIMARY_KEY = "子订单编号"

SHOP_CONFIGS = [
    {"shop_name": "林内官方旗舰店", "db_config": None, "recent_days": 3},
]


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

    for shop_cookie in shop_cookies:
        shop_name = shop_cookie[0]
        cookie = shop_cookie[1]
        db_config = shop_config_by_name.get(shop_name, {}).get("db_config")
        api = TaoXiGongZuoTaiTradeApi(cookie)
        items = api.list_export_order(start_timestamp, end_timestamp)
        if not items:
            logger.warning(f"{shop_name} 商家工作台报表明细无可写入数据")
            continue

        for item in items:
            item["店铺名称"] = shop_name

        with DBManager(db_config=db_config) as db_manager:
            db_manager.update_insert_data(items, TABLE_NAME, primary_key=PRIMARY_KEY)
        logger.info("-" * 100)
    logger.info("*" * 100)
