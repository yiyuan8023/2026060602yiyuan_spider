"""
开发说明：
- 作者：一元
- 创建时间：2026-06-06 13:28:51
- 最近修改：2026-06-08 16:56:21
- 文件用途：采集淘宝联盟服务商合作普通招商中我报名的活动和报名商品数据，解析后写入目标表。
- 业务范围：适用于淘宝联盟服务商合作普通招商报名商品数据，当前按店铺和页码采集，与采集日期无直接关系。
- 依赖入口：调用 API.API_TaoKe.API_TaoKe_MyProducts.TaoKeMyProductApi 获取报名商品数据，使用 select_shop_date 获取店铺 Cookie，使用 DBManager 入库，日志走 extra.logger_。
- 验收方式：修改后执行 py_compile；涉及接口或入库逻辑时先单店铺、单页验证字段解析、主键 sign_up_record 和目标表写入。
- 注意事项：正式运行建议通过 run_job.py 设置项目根路径和 LOG_MODE；不得输出真实 Cookie、签名下载 URL 或数据库敏感配置。
"""

from typing import List

from API.API_TaoKe.API_TaoKe_MyProducts import TaoKeMyProductApi
from database import DBManager
from extra.logger_ import logger
from extra.select_shop_date import select_shop_date


# 最终任务脚本只保留店铺、表名、页码和入库编排；接口逻辑放在 API 层。
TASK_CONFIG = {
    "table_name": "tb_tk_淘宝联盟_服务商合作_普通招商_我报名的活动_报名的商品_202509",
    "site": "淘宝联盟",
    "pages": range(1, 2),
    "shops": [
        {"shop_name": "林内热水器旗舰店", "db_config": "rinnai_py", "recent_days": 1, },  # noqa
        {"shop_name": "林内官方旗舰店", "db_config": "rinnai_py", "recent_days": 1, },  # noqa
    ],
}


def extract_items(response_data: dict) -> List[dict]:
    """从普通招商报名商品接口返回中提取入库字段。"""
    body = response_data.get("data", {}).get("result", [])
    items = []

    for loop_item in body:
        try:
            resource = loop_item.get("resource", [{}])[0] or {}
            item_info = resource.get("itemInfoDTO") or {}
            advertising_unit = loop_item.get("advertisingUnit", {}) or {}

            items.append(
                {
                    "开始时间": loop_item.get("startTime"),
                    "结束时间": loop_item.get("endTime"),
                    "状态": loop_item.get("showStatusDesc"),
                    "审核通过时间": loop_item.get("auditTime"),
                    "团长信息": loop_item.get("campaignCreatorName"),
                    "商品id": item_info.get("itemId"),
                    "商品标题": item_info.get("title"),
                    "campaignId": resource.get("campaignId"),
                    "sign_up_record": resource.get("signUpRecord"),
                    "佣金率": advertising_unit.get("commissionRate"),
                    "服务费率": advertising_unit.get("serviceRate"),
                }
            )
        except Exception as exc:
            logger.warning(f"普通招商报名商品解析失败: {exc}")
            continue

    return items


def build_items(raw_items: List[dict], item_shop_name: str) -> List[dict]:
    """补充店铺名称，并过滤缺少报名记录主键的数据。"""
    result = []
    for item in raw_items:
        sign_up_record = str(item.get("sign_up_record", "")).strip()
        if not sign_up_record:
            continue

        item["店铺名称"] = item_shop_name
        result.append(item)
    return result


if __name__ == "__main__":
    table_name = TASK_CONFIG["table_name"]
    site = TASK_CONFIG["site"]

    for shop_config in TASK_CONFIG["shops"]:
        target_shop_name = shop_config["shop_name"]
        db_config = shop_config["db_config"]
        recent_days = shop_config["recent_days"]

        shop_cookies, _crawl_day_list = select_shop_date(
            table_name,
            site,
            [target_shop_name],
            recent_days,
        )

        for shop_cookie in shop_cookies:
            cookie = shop_cookie[1]
            shop_name = shop_cookie[0]
            api = TaoKeMyProductApi(cookie)

            for page in TASK_CONFIG["pages"]:
                logger.info(f"正在采集【{shop_name}】淘宝联盟普通招商报名商品第 {page} 页数据")
                response_json = api.tb_tk_my_enrolled_products(page)
                items = extract_items(response_json)
                if not items:
                    logger.warning(f"{shop_name},第 {page} 页普通招商报名商品数据为空，跳过入库")
                    continue

                items = build_items(items, shop_name)
                if not items:
                    logger.warning(f"{shop_name},第 {page} 页普通招商报名商品缺少 sign_up_record，跳过入库")
                    continue

                with DBManager(db_config=db_config) as db_manager:
                    db_manager.update_insert_data(
                        items,
                        table_name,
                        primary_key="sign_up_record",
                    )

                logger.info(f"{shop_name},第 {page} 页普通招商报名商品数据已入库")

            logger.info(f"\n{'-' * 100}")

    logger.info(f"\n{'*' * 120}")
