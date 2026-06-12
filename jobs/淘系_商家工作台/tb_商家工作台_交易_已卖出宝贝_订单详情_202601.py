"""
开发说明：
- 作者：一元
- 创建时间：2026-06-06 13:28:51
- 最近修改：2026-06-12 09:17:59
- 文件用途：执行商家工作台交易已卖出宝贝订单详情采集任务，按店铺读取待补充订单并写入消费者视角优惠明细。
- 业务范围：适用于淘系商家工作台交易已卖出宝贝订单详情，当前从 py_tb_消费者视角优惠明细_新增 读取订单编号。
- 依赖入口：使用 API.API_TaoXi_GongZuoTai.TaoXiGongZuoTaiOrderDetailApi、extra.select_shop_date、database.DBManager 和 extra.logger_。
- 验收方式：修改后执行 py_compile；真实请求时用单店铺、少量订单验证订单详情结构、目标表、唯一 key 和请求间隔。
- 注意事项：不在脚本内记录真实 Cookie、数据库密码或订单详情完整敏感响应；未确认前不做大范围真实写库。
"""

import random
from time import sleep

from API.API_TaoXi_GongZuoTai import TaoXiGongZuoTaiOrderDetailApi
from database import DBManager
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date


TABLE_NAME = "tb_商家工作台_交易_已卖出宝贝_订单详情_消费者视角优惠明细_202601"
SOURCE_TABLE_NAME = "py_tb_消费者视角优惠明细_新增"
SITE = "生意参谋"
PRIMARY_KEY = "主订单编号"

SHOP_CONFIGS = [
    {"shop_name": "林内官方旗舰店", "db_config": "rinnai_py", "recent_days": 1},  # noqa
    {"shop_name": "林内热水器旗舰店", "db_config": "rinnai_py", "recent_days": 1},  # noqa
    {"shop_name": "林内品牌折扣店", "db_config": "rinnai_py", "recent_days": 1},  # noqa
    {"shop_name": "智慧家电直销店", "db_config": "rinnai_py", "recent_days": 1},  # noqa
    {"shop_name": "林内厨电旗舰店", "db_config": "rinnai_py", "recent_days": 1},  # noqa
]


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

    for shop_cookie in shop_cookies:
        shop_name = shop_cookie[0]
        cookie = shop_cookie[1]
        db_config = shop_config_by_name.get(shop_name, {}).get("db_config")

        api = TaoXiGongZuoTaiOrderDetailApi(cookie)
        with DBManager(db_config=db_config) as db_manager:
            order_list = db_manager.execute_sql(
                f"select `订单编号` from `{SOURCE_TABLE_NAME}` where `店铺名称`=%s",  # noqa
                (shop_name,),
                fetch=True,
            )

            logger.info(f"{shop_name} 待采集订单数: {len(order_list)}")
            for order_row in order_list:
                order_id = order_row[0]
                items = api.order_discount_details(order_id)
                if not items:
                    logger.warning(f"{shop_name} 订单 {order_id} 无可写入优惠明细")
                    continue

                for item in items:
                    item.update({"店铺名称": shop_name, "主订单编号": order_id})

                db_manager.update_insert_data(items, TABLE_NAME, primary_key=PRIMARY_KEY)
                sleep(random.uniform(1, 5))
        logger.info("-" * 100)
    logger.info("*" * 100)
