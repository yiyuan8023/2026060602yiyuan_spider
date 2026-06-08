# File: pdd_数据中心_服务数据_售后数据
import itertools

from API.API_JingDong.API_Jdsz_Product import JdSzProductAPI

from extra.select_shop_date import select_shop_date
from database import DBManager
from extra.en_to_cn import en_to_cn
from date_utils import get_date_min_max
from extra.logger_ import logger

# noqa: E501
dict_str = {
    "OrdAmt": "成交金额",
    "PV": "浏览量",
    "ShelvesNumSPU": "上架商品数(SPU)",
    "DealCustNum": "成交客户数",
    "AddBuyGoodsNum": "加购商品件数",
    "UV": "访客数",
    "SecondName": "二级类目",
    "DealCustRate": "成交转化率",
    "ShelvesNumSKU": "上架商品数(SKU)",
    "ThirdName": "三级类目",
}

if __name__ == "__main__":
    db_config = None  # noqa
    # db_config = "rinnai_py"  # noqa
    shop_name_list = ["BMW官方旗舰店"]  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "jd_jdsz_商品_类目分析_行业类目"
    site = "京东商智"
    shop_cookies, crawl_day_list = select_shop_date(table_name, site, shop_name_list, 1)

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]
        Obj = JdSzProductAPI(cookie)
        for date in crawl_day_list:

            data_list = []
            res = Obj.fetch_product_analysis__category_analysis(date)
            results = res.get("body", {}).get("data", [])
            data_list1 = en_to_cn(results, dict_str)  # 首层中英文转换
            data_list.append(data_list1)

            for result in results:
                children_results = result.get("children", [])
                data_list2 = en_to_cn(children_results, dict_str)  # 二层中英文转换
                data_list.append(data_list2)

            data_list_open = list(
                itertools.chain.from_iterable(data_list)
            )  # 使用itertools.chain展平嵌套列表

            items = []
            for item in data_list_open:
                item.update(
                    {
                        "店铺名称": shop_name,
                        "统计日期": date,
                    }
                )
                item["key"] = (
                    f"{item['店铺名称']}_{item['二级类目']}_{item['三级类目']}_{item['统计日期']}"
                )
                items.append(item)
            print(items)

            DBManager(db_config=db_config).update_insert_data(
                items, table_name, primary_key="key"
            )
            logger.info(f"{shop_name}_{date}数据已入库")
        logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")
