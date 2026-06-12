import random
from time import sleep

from API.API_TaoXi_SYCM.SelfAnalysis import SelfAnalysis  # noqa
from database import DBManager
from date_utils import get_date
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date

SHOP_CONFIGS = [
    {
        "shop_name": "林内官方旗舰店",
        "db_config": "rinnai_py",  # NOQA
        "recent_days": 3,
        "shop_id": "20893",
    },
]


def build_items(raw_items):
    """为自助取数商品流量来源明细生成唯一 key。"""
    result = []
    for item in raw_items:
        item["key"] = (
            f"{item['商品ID']}_{item['店铺名称']}_{item['统计日期']}_"
            f"{item['一级流量来源']}_{item['二级流量来源']}_{item['三级流量来源']}"
        )
        result.append(item)
    return result


if __name__ == "__main__":
    shop_name_list = [shop_config["shop_name"] for shop_config in SHOP_CONFIGS]
    shop_config_by_name = {shop_config["shop_name"]: shop_config for shop_config in SHOP_CONFIGS}
    recent_days = max(shop_config["recent_days"] for shop_config in SHOP_CONFIGS)

    table_name = "tb_sycm_自助分析_取数_商品_流量来源_所有商品_格式化_202507"  # noqa
    site = "生意参谋"
    shop_cookies, crawl_day_list = select_shop_date(table_name, site, shop_name_list, recent_days)

    for shop_cookie in shop_cookies:
        cookie = shop_cookie[1]
        shop_name = shop_cookie[0]
        shop_config = shop_config_by_name.get(shop_name, {})
        db_config = shop_config.get("db_config")
        shop_id = shop_config.get("shop_id")
        if not shop_id:
            logger.warning(f"{shop_name} 未配置生意参谋 shop_id，跳过")
            continue

        api = SelfAnalysis(cookie)
        for day in crawl_day_list:
            sleep(random.uniform(0.5, 2))
            start_date = end_data = get_date(day)
            logger.info(f"正在采集{shop_name},{start_date}——{end_data}的数据")

            report_id = api.create_report(shop_id, start_date, end_data)
            if not report_id:
                logger.warning(f"{shop_name},{day} 自助取数创建任务失败，跳过")
                continue

            logger.success(f"创建任务成功，report_id={report_id}")
            items = api.download_report_excel(report_id)
            items = build_items(items or [])
            if not items:
                logger.warning(f"{shop_name},{day} 自助取数下载数据为空，跳过入库")
                continue

            with DBManager(db_config=db_config) as db_manager:
                db_manager.update_insert_data(items, table_name, primary_key="key")

            logger.info("-" * 100)
            logger.info(f"{shop_name},{day}的数据已入库")
            logger.info(f"\n{'*' * 120}")

# python tb_sycm_自助分析_取数_商品_流量来源_所有商品_格式化.py --start-date=2024-07-20 --end-date=2025-07-31  # noqa
