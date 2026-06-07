# File: 生参商品_品类360_流量分析_流量来源

from API.API_ShengCan.goods import Goods
from extra.select_shop_date import select_shop_date
from database import DBManager
from extra.extra_date import get_month_first_and_last_day
from extra.logger_ import logger

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


def analyzing_res(res_json):
    if res_json:
        data = res_json["data"]
        items_en = analyzing_(data)
        items = []
        for item_en in items_en:
            item = {"一级流量来源": "", "二级流量来源": "", "三级流量来源": ""}
            for k, v in cn_en_mappings.items():
                item[k] = item_en.get(v)
            item.update(
                {
                    "店铺名称": shop_name,
                    "统计日期": dateRange,
                    "日期类型": "month",
                    "类目id": cateId,
                    "类目": cateName,
                }
            )
            item["key"] = (
                f"{item['店铺名称']}_{item['统计日期']}_{item['日期类型']}_{item['一级流量来源']}_{item['二级流量来源']}_{item['三级流量来源']}"
            )
            items.append(item)
        DBManager().update_insert_data(items, db_table_name, primary_key="key")

    else:
        logger.info("数据为空")


if __name__ == "__main__":

    db_table_name = "tb_sycm_商品_品类360_流量分析_流量来源_202504"  # noqa

    shop_cate_info = {
        "林内官方旗舰店": [{"50022703": "大家电>热水器>燃气热水器"}],
        # '林内官方旗舰店': [{"50022703":"大家电>热水器>燃气热水器","50005928":"大家电>洗碗机"}],
        # '林内厨电旗舰店': [{"50022703":"大家电>热水器>燃气热水器"}],
    }
    shop_name_list = shop_cate_info.keys()
    site = "生意参谋"

    shop_cookies, crawl_day_list = select_shop_date(
        db_table_name, site, shop_name_list, recent_period=3, period_type="month"
    )

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]
        for k, v in shop_cate_info.get(shop_name)[0].items():
            cateId = k
            cateName = v
            GoodObj = Goods(cookie)
            for day in crawl_day_list:
                start_date, end_data = get_month_first_and_last_day(
                    day
                )  # 获取本月第一天和最后一天
                dateRange = f" {start_date}|{end_data}"
                logger.info(f"正在采集{dateRange}的月数据")
                res_json = GoodObj.category_360__flow_from(dateRange, cateId)
                print(f"请求参数: dateRange={dateRange}, cateId={cateId}")
                # print(res_json)
                analyzing_res(res_json)
        # print(res_json)

# python tb_sycm_商品_品类360_流量分析_流量来源_202504.py --mode=monthly --month=01
