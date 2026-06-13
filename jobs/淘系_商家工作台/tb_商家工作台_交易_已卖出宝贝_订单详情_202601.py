"""
开发说明：
- 作者：一元
- 创建时间：2026-06-06 13:28:51
- 最近修改：2026-06-12 14:43:20
- 文件用途：执行商家工作台交易已卖出宝贝订单详情采集任务，按店铺读取待补充订单，并发查询订单详情后批量写入优惠明细业务表和 json_data 分表。
- 业务范围：适用于淘系商家工作台交易已卖出宝贝订单详情，当前从 py_tb_消费者视角优惠明细_新增 读取订单编号，原始响应写入 json_data 分表。
- 依赖入口：使用 API.API_TaoXi_GongZuoTai.TaoXiGongZuoTaiOrderDetailApi、extra.select_shop_date、database.DBManager 和 extra.logger_。
- 验收方式：修改后执行 py_compile；真实请求时用单店铺、少量订单验证订单详情结构、目标表、唯一 key 和请求间隔。
- 注意事项：不在脚本内记录真实 Cookie、数据库密码或订单详情完整敏感响应；未确认前不做大范围真实写库。
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from math import ceil
from time import sleep

from API.API_TaoXi_GongZuoTai import TaoXiGongZuoTaiOrderDetailApi
from database import DBManager
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date


TABLE_NAME = "tb_商家工作台_交易_已卖出宝贝_订单详情_消费者视角优惠明细_202601"
JSON_TABLE_NAME = "tb_商家工作台_交易_已卖出宝贝_订单详情_json_data_202601"
SOURCE_TABLE_NAME = "py_tb_消费者视角优惠明细_新增"
SITE = "生意参谋"
PRIMARY_KEY = "主订单编号"

SHOP_CONFIGS = [
    {"shop_name": "林内官方旗舰店", "db_config": "rinnai_py", "recent_days": 1, "max_workers": 5, "batch_size": 50},  # noqa
    {"shop_name": "林内热水器旗舰店", "db_config": "rinnai_py", "recent_days": 1, "max_workers": 3, "batch_size": 20},  # noqa
    {"shop_name": "林内品牌折扣店", "db_config": "rinnai_py", "recent_days": 1, "max_workers": 3, "batch_size": 20},  # noqa
    {"shop_name": "智慧家电直销店", "db_config": "rinnai_py", "recent_days": 1, "max_workers": 3, "batch_size": 20},  # noqa
    {"shop_name": "林内厨电旗舰店", "db_config": "rinnai_py", "recent_days": 1, "max_workers": 3, "batch_size": 20},  # noqa
]


def fetch_order_detail(cookie, order_id):
    """线程内只负责请求和解析订单详情，不持有数据库连接。"""
    api = TaoXiGongZuoTaiOrderDetailApi(cookie)
    return order_id, api.order_discount_details(order_id)


def build_write_items(order_result, shop_name, order_id):
    """把 API 显式返回结果组装成业务表记录和 json_data 分表记录。"""
    if not order_result["business_items"]:
        raise ValueError(f"订单 {order_id} 未返回 business_items")

    business_items = []
    for raw_item in order_result["business_items"]:
        item = dict(raw_item)
        item.update({"店铺名称": shop_name, "主订单编号": order_id})
        business_items.append(item)

    json_items = [
        {
            "主订单编号": order_id,
            "店铺名称": shop_name,
            "json_data": order_result["json_data"],
            "备注": business_items[0].get("备注") if business_items else None,
        }
    ]

    return business_items, json_items


def flush_write_buffers(db_manager, business_buffer, json_buffer):
    """主线程批量写入两张表，写完清空缓冲。"""
    if not business_buffer and not json_buffer:
        return

    db_manager.update_insert_data(business_buffer, TABLE_NAME, primary_key=PRIMARY_KEY)
    db_manager.update_insert_data(json_buffer, JSON_TABLE_NAME, primary_key=PRIMARY_KEY)
    business_buffer.clear()
    json_buffer.clear()


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
        shop_config = shop_config_by_name.get(shop_name, {})
        db_config = shop_config.get("db_config")
        max_workers = shop_config.get("max_workers", 3)
        batch_size = shop_config.get("batch_size", 20)

        with DBManager(db_config=db_config) as db_manager:
            order_list = db_manager.execute_sql(
                f"select `订单编号` from `{SOURCE_TABLE_NAME}` where `店铺名称`=%s",  # noqa
                (shop_name,),
                fetch=True,
            )

            logger.info(f"{shop_name} 待采集订单数: {len(order_list)}")
            if not order_list:
                logger.info(f"{shop_name} 无待采集订单")
                continue

            order_ids = [order_row[0] for order_row in order_list]
            total_batches = ceil(len(order_ids) / batch_size)
            business_buffer = []
            json_buffer = []
            completed_count = 0

            logger.info(
                f"{shop_name} 开始并发采集订单详情: max_workers={max_workers}, batch_size={batch_size}"
            )
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                for batch_index, start_index in enumerate(
                    range(0, len(order_ids), batch_size),
                    1,
                ):
                    batch_order_ids = order_ids[start_index : start_index + batch_size]
                    future_map = {
                        executor.submit(fetch_order_detail, cookie, order_id): order_id
                        for order_id in batch_order_ids
                    }

                    for future in as_completed(future_map):
                        order_id = future_map[future]
                        try:
                            result_order_id, order_result = future.result()
                            business_items, json_items = build_write_items(
                                order_result,
                                shop_name,
                                result_order_id,
                            )
                        except Exception:
                            flush_write_buffers(db_manager, business_buffer, json_buffer)
                            logger.exception(f"{shop_name} 订单 {order_id} 并发采集失败")
                            raise

                        business_buffer.extend(business_items)
                        json_buffer.extend(json_items)
                        completed_count += 1

                    flush_write_buffers(db_manager, business_buffer, json_buffer)
                    logger.info(
                        f"{shop_name} 已批量写入 {completed_count}/{len(order_ids)} 单，"
                        f"批次 {batch_index}/{total_batches}"
                    )
                    sleep(1)

            logger.info(f"{shop_name} 订单详情采集完成: {completed_count}/{len(order_ids)}")
        logger.info("-" * 100)
    logger.info("*" * 100)
