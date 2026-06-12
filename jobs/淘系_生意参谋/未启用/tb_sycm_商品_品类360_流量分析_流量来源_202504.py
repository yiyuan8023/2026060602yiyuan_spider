# File: 生参商品_品类360_流量分析_流量来源

from API.API_TaoXi_SYCM.goods import Goods  # noqa
from extra.select_shop_date import select_shop_date
from database import DBManager
from date_utils import get_month_first_and_last_day
from extra.logger_ import logger

SHOP_CONFIGS = [
    {
        "shop_name": "林内官方旗舰店",
        "db_config": None,
        "recent_days": 3,
        "cate_info": {"50022703": "大家电>热水器>燃气热水器"},
    },
]

cn_en_mappings = {
    "商品访客数": "itmUv",
    "商品加购人数": "itemCartByrCnt",
    "商品收藏人数": "itemCltByrCnt",
    "支付买家数": "payByrCnt",
    "下单买家数": "crtByrCnt",
    "访问收藏转化率": "visitCltRate",
    "访问加购转化率": "visitCartRate",
    "下单转化率": "crtRate",
    "支付转化率": "payRate",
    "支付金额": "payAmt",
    "访客平均价值": "uvAvgValue",
    "一级流量来源": "pageName_1",
    "二级流量来源": "pageName_2",
    "三级流量来源": "pageName_3",
    "子流量来源id": "pageId",
    "层级": "pageLevel",
}


def analyzing_(data, d=None):
    if d is None:
        d = {}
    items = []
    for i in data:
        item = {}
        add_dict = {}
        for k, v in i.items():
            if k == "pageName":
                item[f"{k}_{i['pageLevel']['value']}"] = v["value"]
                add_dict[f"{k}_{i['pageLevel']['value']}"] = v["value"]
            else:
                if "value" in v and k != "children":
                    item[k] = v["value"]
        item.update(d)
        items.append(item)
        if "children" in i.keys():
            children = i["children"]
            if children:
                # 递归处理子节点，并将结果合并到 items 中
                add_dict.update(d) if d else add_dict
                items += analyzing_(i["children"], add_dict)
    return items


def build_category_flow_items(
        response_data,
        item_shop_name,
        date_range,
        cate_id,
        cate_name,
):
    """解析品类360树形流量来源，并补充任务维度和唯一 key。"""
    if not response_data or not response_data.get("data"):
        return []

    items_en = analyzing_(response_data["data"])
    items = []
    for item_en in items_en:
        item = {"一级流量来源": "", "二级流量来源": "", "三级流量来源": ""}
        for cn_name, en_name in cn_en_mappings.items():
            item[cn_name] = item_en.get(en_name)
        item.update(
            {
                "店铺名称": item_shop_name,
                "统计日期": date_range,
                "日期类型": "month",
                "类目id": cate_id,
                "类目": cate_name,
            }
        )
        item["key"] = (
            f"{item['店铺名称']}_{item['统计日期']}_{item['日期类型']}_"
            f"{item['一级流量来源']}_{item['二级流量来源']}_{item['三级流量来源']}"
        )
        items.append(item)
    return items


if __name__ == "__main__":

    db_table_name = "tb_sycm_商品_品类360_流量分析_流量来源_202504"  # noqa

    shop_name_list = [shop_config["shop_name"] for shop_config in SHOP_CONFIGS]
    shop_config_by_name = {shop_config["shop_name"]: shop_config for shop_config in SHOP_CONFIGS}
    recent_days = max(shop_config["recent_days"] for shop_config in SHOP_CONFIGS)
    site = "生意参谋"

    shop_cookies, crawl_day_list = select_shop_date(
        db_table_name, site, shop_name_list, recent_days=recent_days, period_type="month"
    )

    for shop_cookie in shop_cookies:
        cookie = shop_cookie[1]
        shop_name = shop_cookie[0]
        shop_config = shop_config_by_name.get(shop_name, {})
        db_config = shop_config.get("db_config")
        GoodObj = Goods(cookie)
        for cateId, cateName in shop_config.get("cate_info", {}).items():
            for day in crawl_day_list:
                start_date, end_data = get_month_first_and_last_day(
                    day
                )  # 获取本月第一天和最后一天
                dateRange = f"{start_date}|{end_data}"
                logger.info(f"正在采集{dateRange}的月数据")
                res_json = GoodObj.category_360__flow_from(dateRange, cateId)
                logger.info(f"请求参数: dateRange={dateRange}, cateId={cateId}")
                items = build_category_flow_items(
                    res_json,
                    shop_name,
                    dateRange,
                    cateId,
                    cateName,
                )
                if not items:
                    logger.warning(f"{shop_name},{dateRange},{cateId} 品类360流量来源数据为空")
                    continue
                with DBManager(db_config=db_config) as db_manager:
                    db_manager.update_insert_data(items, db_table_name, primary_key="key")

# python tb_sycm_商品_品类360_流量分析_流量来源_202504.py --mode=monthly --month=01  # noqa
