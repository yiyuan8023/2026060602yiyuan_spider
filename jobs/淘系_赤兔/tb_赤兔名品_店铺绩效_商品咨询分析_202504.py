"""
开发说明：
- 作者：一元
- 创建时间：2026-06-10 18:00:00
- 最近修改：2026-06-10 18:00:00
- 文件用途：采集赤兔名品店铺绩效商品咨询分析数据，按店铺和统计日期补充业务字段、生成唯一 key 后入库。
- 业务范围：适用于赤兔名品店铺绩效商品咨询分析报表，目标表为 tb_赤兔名品_店铺绩效_商品咨询分析_202504。
- 依赖入口：调用 API.API_ChiTu.API_Chitu_Shop_Performance 导出报表，使用 API.API_ChiTu.API_Chitu_Login 生成赤兔 Cookie，使用 select_shop_date 获取店铺和日期，使用 DBManager 入库，日志走 extra.logger_。
- 验收方式：修改后执行 py_compile；真实采集前先单店铺、单日期验证报表导出、字段补充、唯一 key 和目标表写入。
- 注意事项：运行时会通过赤兔 Cookie 导出报表，Cookie 失效时可能通过 Playwright 使用生意参谋 Cookie 重新授权；不得输出真实 Cookie、赤兔密码、授权信息或导出文件内容。
"""

from API.API_ChiTu import ChituAPIError, ChituShopPerformanceAPI, get_chitu_cookie_header
from database import DBManager
from date_utils import get_date
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date


TABLE_NAME = "tb_赤兔名品_店铺绩效_商品咨询分析_202504"
SITE = "生意参谋"
RECENT_DAYS = 3

# 空列表表示沿用 select_shop_date 的规则采集当前站点全部店铺；需要限定店铺时按三件套补充。
SHOP_CONFIGS = [
    {
        "shop_name": "林内官方旗舰店",
        "db_config": None,
        "recent_days": 3,
        "chitu_password": "123456",
    },
]


def build_items(raw_items, item_shop_name, stat_day):
    """过滤汇总/均值行，补充店铺、统计日期和商品咨询分析唯一 key。"""
    result = []
    for item in raw_items:
        item_id = str(item.get("商品编号", "")).strip()
        if not item_id or item_id in {"汇总", "均值"}:
            continue

        item.update({"店铺名称": item_shop_name, "统计日期": stat_day})
        item["key"] = f"{item_shop_name}_{item_id}_{stat_day}"
        result.append(item)
    return result


def create_chitu_api(item_shop_name, source_cookie, chitu_password):
    """使用生意参谋 Cookie 准备赤兔 Cookie，并返回店铺绩效 API 对象。"""
    cookie_str = get_chitu_cookie_header(item_shop_name, source_cookie)
    return ChituShopPerformanceAPI(
        cookie_str,
        chitu_password,
        shop_name=item_shop_name,
    )


if __name__ == "__main__":
    shop_name_list = [shop_config["shop_name"] for shop_config in SHOP_CONFIGS]
    shop_config_by_name = {shop_config["shop_name"]: shop_config for shop_config in SHOP_CONFIGS}
    recent_days = max((shop_config["recent_days"] for shop_config in SHOP_CONFIGS), default=RECENT_DAYS)

    shop_cookies, crawl_day_list = select_shop_date(TABLE_NAME, SITE, shop_name_list, recent_days)

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
            logger.error(f"{shop_name} 赤兔店铺绩效 API 初始化失败: {exc}")
            continue

        for day in crawl_day_list:
            stat_day = get_date(day)
            logger.info(f"开始采集{shop_name} 赤兔店铺绩效商品咨询分析 {stat_day} 数据")
            try:
                raw_items = api.product_consultation_analysis(stat_day, stat_day)
            except ChituAPIError as exc:
                logger.error(f"{shop_name},{stat_day} 赤兔商品咨询分析导出失败: {exc}")
                continue

            items = build_items(raw_items or [], shop_name, stat_day)
            if not items:
                logger.warning(f"{shop_name},{stat_day} 赤兔商品咨询分析数据为空，跳过入库")
                continue

            with DBManager(db_config=db_config) as db_manager:
                db_manager.update_insert_data(items, TABLE_NAME, primary_key="key")

            logger.info(f"{shop_name},{stat_day} 赤兔商品咨询分析已入库")
            logger.info("-" * 100)

    logger.info("*" * 100)

# python run_job.py "jobs\淘系_赤兔\tb_赤兔名品_店铺绩效_商品咨询分析_202504.py" --log-mode both --start-date=2025-05-01 --end-date=2025-06-25
