"""
开发说明：
- 作者：一元
- 创建时间：2026-06-10 16:23:18
- 最近修改：2026-06-10 16:23:18
- 文件用途：采集赤兔名品一目了然的店铺报表全字段数据，按店铺和日期补充业务字段、生成唯一 key 后入库。
- 业务范围：适用于赤兔名品一目了然「勿删店铺绩效」报表，目标表为 tb_赤兔名品_一目了然_店铺报表全字段_202509。
- 依赖入口：调用 API.API_ChiTu.API_Chitu_Clear_A_Glance 导出报表，使用 API.API_ChiTu.API_Chitu_Login 生成赤兔 Cookie，使用 select_shop_date 获取店铺和日期，使用 DBManager 入库，日志走 extra.logger_。
- 验收方式：修改后执行 py_compile；真实采集前先单店铺、单日期验证报表导出、字段补充、唯一 key 和目标表写入。
- 注意事项：运行时会通过 Playwright 使用淘宝 Cookie 授权赤兔；不得输出真实 Cookie、赤兔密码、授权信息或导出文件内容；未经确认不做大范围真实写库。
"""

from API.API_ChiTu import ChituAPIError, ChituClearAGlanceAPI, get_chitu_cookie_header
from database import DBManager
from date_utils import get_date_min_max, get_split_date_range
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date

TABLE_NAME = "tb_赤兔名品_一目了然_店铺报表全字段_202509"
SITE = "生意参谋"
RECENT_DAYS = 1
DATE_RANGE_INTERVAL_DAYS = 30

# 空列表表示沿用 select_shop_date 的规则采集当前站点全部店铺；需要限定店铺时按三件套补充。
SHOP_CONFIGS = [
    {
        "shop_name": "林内官方旗舰店",
        "db_config": None,
        "recent_days": 1,
        "report_name": "勿删_店铺_IT",
        "chitu_password": "123456",
    },
]


def build_items(raw_items, item_shop_name):
    """过滤汇总/均值行，补充店铺、日期类型和店铺报表唯一 key。"""
    result = []
    for item in raw_items:
        stat_day = str(item.get("日期", "")).strip()
        if not stat_day or stat_day in {"汇总", "均值"}:
            continue

        item.update({"店铺名称": item_shop_name, "日期类型": "day"})
        item["key"] = f"{item_shop_name}_{stat_day}_{item['日期类型']}"
        result.append(item)
    return result


def create_chitu_api(item_shop_name, source_cookie, chitu_password):
    """使用淘宝 Cookie 授权赤兔，并返回一目了然 API 对象。"""
    cookie_str = get_chitu_cookie_header(item_shop_name, source_cookie)
    return ChituClearAGlanceAPI(
        cookie_str,
        chitu_password,
        shop_name=item_shop_name,
    )


if __name__ == "__main__":
    shop_name_list = [shop_config["shop_name"] for shop_config in SHOP_CONFIGS]
    shop_config_by_name = {shop_config["shop_name"]: shop_config for shop_config in SHOP_CONFIGS}
    recent_days = max((shop_config["recent_days"] for shop_config in SHOP_CONFIGS), default=RECENT_DAYS)

    shop_cookies, crawl_day_list = select_shop_date(TABLE_NAME, SITE, shop_name_list, recent_days)
    min_date, max_date = get_date_min_max(crawl_day_list)
    date_ranges = get_split_date_range(min_date, max_date, interval_days=DATE_RANGE_INTERVAL_DAYS)

    for shop_cookie in shop_cookies:
        shop_name = shop_cookie[0]
        cookie = shop_cookie[2] or shop_cookie[1]
        shop_config = shop_config_by_name.get(shop_name, {})
        db_config = shop_config.get("db_config")
        chitu_password = shop_config.get("chitu_password")
        if not chitu_password:
            logger.error(f"{shop_name} 未配置赤兔校验密码，跳过")
            continue

        try:
            api = create_chitu_api(shop_name, cookie, chitu_password)
        except ChituAPIError as exc:
            logger.error(f"{shop_name} 赤兔 API 初始化失败: {exc}")
            continue

        report_name = shop_config.get("report_name")
        if not report_name:
            logger.error(f"{shop_name} 未配置赤兔店铺报表名称，跳过")
            continue

        for start_date, end_date in date_ranges:
            logger.info(f"开始采集{shop_name} 赤兔一目了然店铺报表 {start_date}-{end_date} 数据")
            try:
                raw_items = api.export_table(report_name, start_date, end_date)
            except ChituAPIError as exc:
                logger.error(
                    f"{shop_name},{start_date}-{end_date} 赤兔店铺报表导出失败: {exc}"
                )
                continue
            items = build_items(raw_items or [], shop_name)
            if not items:
                logger.warning(f"{shop_name},{start_date}-{end_date} 赤兔一目了然店铺报表数据为空，跳过入库")
                continue

            with DBManager(db_config=db_config) as db_manager:
                db_manager.update_insert_data(items, TABLE_NAME, primary_key="key")

            logger.info(f"{shop_name},{start_date}-{end_date} 赤兔一目了然店铺报表已入库")
            logger.info("-" * 100)

    logger.info("*" * 100)

# python run_job.py "jobs\淘系_赤兔\tb_赤兔名品_一目了然_店铺报表全字段_202509.py" --log-mode both --start-date=2025-09-01 --end-date=2025-09-30
