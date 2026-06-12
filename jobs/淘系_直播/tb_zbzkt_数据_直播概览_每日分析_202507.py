"""
开发说明：
- 作者：一元
- 创建时间：2026-06-06 13:28:51
- 最近修改：2026-06-10 21:05:00
- 文件用途：采集淘宝直播中控台直播概览每日分析数据，补充店铺、日期类型和唯一 key 后写入目标表。
- 业务范围：适用于淘系直播中控台直播概览页面，按店铺和统计日期采集每日分析指标。
- 依赖入口：调用 API.API_TaoXi_ZhiBo.TaoXiZhiBoLiveOverviewApi 获取原始数据，使用 get_taoxi_zhibo_cookie_header 准备直播 Cookie，使用 build_live_overview_items 生成入库数据，使用 select_shop_date 获取店铺和日期，使用 DBManager 入库。
- 验收方式：修改后执行 py_compile；真实采集时先单店铺、单日期验证 Cookie 复用/刷新、接口返回、raw_ 新增字段自动补列和目标表写入。
- 注意事项：正式运行建议通过 run_job.py 设置项目根路径和 LOG_MODE；不得输出真实 Cookie、签名 URL 或数据库敏感配置。
"""

from API.API_TaoXi_ZhiBo import TaoXiZhiBoLiveOverviewApi, get_taoxi_zhibo_cookie_header
from API.API_TaoXi_ZhiBo.parser_live_overview import build_live_overview_items
from database import DBManager
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date


# 任务脚本只保留店铺、表名、日期选择和入库编排；接口、Cookie、字段解析分别放到 API 层。
TASK_CONFIG = {
    "table_name": "tb_zbzkt_数据_直播概览_每日分析_202507",
    "source_site": "生意参谋",
    "date_type": "day",
    "shops": [
        {"shop_name": "林内官方旗舰店", "db_config": "rinnai_py", "recent_days": 1},  # noqa
    ],
}


if __name__ == "__main__":
    table_name = TASK_CONFIG["table_name"]
    source_site = TASK_CONFIG["source_site"]
    date_type = TASK_CONFIG["date_type"]

    for shop_config in TASK_CONFIG["shops"]:
        target_shop_name = shop_config["shop_name"]
        db_config = shop_config["db_config"]
        recent_days = shop_config["recent_days"]

        # 使用生意参谋作为来源站点，便于直播 Cookie 失效时自动派生刷新。
        shop_cookies, crawl_day_list = select_shop_date(
            table_name,
            source_site,
            [target_shop_name],
            recent_days,
        )

        for shop_cookie in shop_cookies:
            shop_name = shop_cookie[0]
            sycm_cookie_json = shop_cookie[2]
            cookie = get_taoxi_zhibo_cookie_header(shop_name, sycm_cookie=sycm_cookie_json)
            api = TaoXiZhiBoLiveOverviewApi(cookie)

            for day in crawl_day_list:
                logger.info(f"正在采集【{shop_name}】{day} 淘宝直播概览每日分析数据")
                raw_items = api.live_overview_items(day, day)
                if not raw_items:
                    logger.warning(f"{shop_name},{day} 淘宝直播概览每日分析数据为空，跳过入库")
                    continue

                items = build_live_overview_items(raw_items, shop_name, day, date_type)
                if not items:
                    logger.warning(f"{shop_name},{day} 淘宝直播概览每日分析缺少统计日期，跳过入库")
                    continue

                with DBManager(db_config=db_config) as db_manager:
                    db_manager.update_insert_data(items, table_name, primary_key="key")

                logger.info(f"{shop_name},{day} 淘宝直播概览每日分析数据已入库")
                logger.info(f"\n{'-' * 100}")

    logger.info(f"\n{'*' * 120}")
