from API.API_TaoXi_SYCM.Flow import Flow  # noqa

from extra.select_shop_date import select_shop_date
from database import DBManager

from extra.logger_ import logger

SHOP_CONFIGS = [
    {"shop_name": "林内热水器旗舰店", "db_config": "rinnai_py", "recent_days": 7},  # NOQA
]


def build_items(raw_items, item_id, item_shop_name, stat_day):
    """补充旧版商品来源流量维度，并生成唯一 key。"""
    result = []
    for item in raw_items:
        item.update(
            {
                "商品id": item_id,
                "店铺名称": item_shop_name,
                "统计日期": stat_day,
                "日期类型": "day",
            }
        )
        item["key"] = (
            f"{item['商品id']}_{item['店铺名称']}_{stat_day}_{item['日期类型']}_"
            f"{item['一级来源']}_{item['二级来源']}_{item['三级来源']}"
        )
        result.append(item)
    return result


if __name__ == "__main__":
    shop_name_list = [shop_config["shop_name"] for shop_config in SHOP_CONFIGS]
    shop_config_by_name = {shop_config["shop_name"]: shop_config for shop_config in SHOP_CONFIGS}
    recent_days = max(shop_config["recent_days"] for shop_config in SHOP_CONFIGS)
    table_name = "tb_sycm_流量_商品来源_商品来源流量_旧版_202504"  # noqa
    site = "生意参谋"
    shop_cookies, crawl_day_list = select_shop_date(
        table_name, site, shop_name_list, recent_days
    )
    # crawl_day_list = ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"]
    shop_item_ids = {
        "林内热水器旗舰店": [
            "732897762742",
            "793864718809",
            "763629523250",
            "763629523250",
            "1003352210602",
        ],
        # '林内厨电旗舰店': ["673717490518"]
    }

    for shop_cookie in shop_cookies:
        cookie = shop_cookie[1]
        shop_name = shop_cookie[0]
        db_config = shop_config_by_name.get(shop_name, {}).get("db_config")
        Obj = Flow(cookie)
        for day in crawl_day_list:
            item_ids = shop_item_ids.get(shop_name, [])
            if not item_ids:
                logger.warning(f"{shop_name} 未配置商品ID，跳过")
                continue
            for item_id in item_ids:
                logger.info(f"正在采集{shop_name},{day},{item_id}的数据")
                items = Obj.goods_from__listen_good_flow_day(item_id, day)
                items = build_items(items or [], item_id, shop_name, day)
                if not items:
                    logger.warning(f"{shop_name},{day},{item_id} 旧版商品来源流量数据为空，跳过入库")
                    continue

                with DBManager(db_config=db_config) as db_manager:
                    db_manager.update_insert_data(items, table_name, primary_key="key")

                logger.info(f"{shop_name},{day}的数据已入库")
            logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")

# python tb_sycm_流量_商品来源_商品来源流量_旧版_202504.py --start-date=2025-03-27 --end-date=2025-04-18 # noqa
