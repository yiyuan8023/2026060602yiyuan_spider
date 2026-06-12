from API.API_TaoXi_SYCM.Flow import Flow  # noqa
from extra.select_shop_date import select_shop_date
from database import DBManager
from extra.logger_ import logger

SHOP_CONFIGS = [
    {"shop_name": "林内官方旗舰店", "db_config": None, "recent_days": 1},
    {"shop_name": "林内厨电旗舰店", "db_config": None, "recent_days": 1},
]

SHEET_TABLE_INDEX = {
    "全店流量来源": 0,
    "经营优势来源渠道": 1,
    "分载体流量来源": 2,
}


def build_sheet_items(sheet_name, raw_items, item_shop_name, stat_day):
    """补充全店流量来源各工作表维度，并生成对应唯一 key。"""
    result = []
    for item in raw_items:
        item.update(
            {
                "sheet_name": sheet_name,
                "店铺名称": item_shop_name,
                "统计日期": stat_day,
                "日期类型": "day",
            }
        )
        if sheet_name == "经营优势来源渠道":
            item["key"] = (
                f"{item['店铺名称']}_{stat_day}_day_{item.get('流量载体')}_"
                f"{item.get('来源名称')}"
            )
        else:
            item["key"] = (
                f"{item['店铺名称']}_{stat_day}_day_{item.get('流量载体')}_"
                f"{item.get('一级来源')}_{item.get('二级来源')}_{item.get('三级来源')}"
            )
        result.append(item)
    return result


if __name__ == "__main__":
    shop_name_list = [shop_config["shop_name"] for shop_config in SHOP_CONFIGS]
    shop_config_by_name = {shop_config["shop_name"]: shop_config for shop_config in SHOP_CONFIGS}
    recent_days = max(shop_config["recent_days"] for shop_config in SHOP_CONFIGS)
    db_table_name = [
        "tb_sycm_流量_店铺来源_流量来源构成_全店_全店流量来源_202504",  # noqa
        "tb_sycm_流量_店铺来源_流量来源构成_全店_经营优势来源渠道_202504",  # noqa
        "tb_sycm_流量_店铺来源_流量来源构成_全店_分载体流量来源_202504",  # noqa
    ]

    site = "淘系_生意参谋"

    shop_cookies, crawl_day_list = select_shop_date(
        db_table_name, site, shop_name_list, recent_days
    )

    for shop_cookie in shop_cookies:
        cookie = shop_cookie[1]
        shop_name = shop_cookie[0]
        db_config = shop_config_by_name.get(shop_name, {}).get("db_config")
        Obj = Flow(cookie)
        for day in crawl_day_list:
            logger.info(f"正在采集{shop_name},{day}的数据")
            items_dict = Obj.shop_from__flow_from_build__shop_flow_day(day)
            if not items_dict:
                logger.warning(f"{shop_name},{day} 全店流量来源数据为空，跳过入库")
                continue
            for sheet_name, items in items_dict.items():
                table_index = SHEET_TABLE_INDEX.get(sheet_name)
                if table_index is None:
                    logger.warning(f"{shop_name},{day} 未配置工作表入库表名: {sheet_name}")
                    continue

                items = build_sheet_items(sheet_name, items or [], shop_name, day)
                if not items:
                    logger.warning(f"{shop_name},{day},{sheet_name} 数据为空，跳过入库")
                    continue

                with DBManager(db_config=db_config) as db_manager:
                    db_manager.update_insert_data(
                        items, db_table_name[table_index], primary_key="key"
                    )

            logger.info(f"{shop_name},{day}的数据已入库")
            logger.info("-" * 100)
        logger.info(f"\n{'*' * 120}")

# python tb_sycm_流量_店铺来源_流量来源构成_全店流量_新版.py --start-date=2025-03-27 --end-date=2025-04-18 # noqa
