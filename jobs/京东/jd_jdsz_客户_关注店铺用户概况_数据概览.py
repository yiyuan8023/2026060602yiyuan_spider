from API.API_JingDong.API_Jdsz_Product import JdSzProductAPI
from extra.select_shop_date import select_shop_date
from database import DBManager
from extra.en_to_cn import en_to_cn
from extra.logger_ import logger

# noqa: E501
dict_str = {
    "VCustNum": "有效用户总数",
    "VNewCustNum": "有效新增用户数",
    "VNetCustNum": "有效净增用户数",
    "ShopUV": "进店访客数",
    "ShopPV": "进店浏览量",
    "DetPVRate": "商详流量用户占比",
    "ShopPVRate": "店铺流量用户占比",
    "OrdCustNum": "成交客户数",
    "OrdNum": "成交单量",
    "OrdAmt": "成交金额",
    "CustPriceAvg": "成交客单价",
    "ToOrdRate": "成交转化率",
    "The30RepBuyRate": "30天复购率",
    "The90RepBuyRate": "90天复购率",
}

if __name__ == "__main__":
    db_config = None  # noqa
    # db_config = "rinnai_py"  # noqa
    shop_name_list = ["BMW官方旗舰店"]  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "jd_jdsz_客户_关注店铺用户概况_数据概览"
    site = "京东商智"
    shop_cookies, crawl_day_list = select_shop_date(
        table_name, site, shop_name_list, 30
    )

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]

        Obj = JdSzProductAPI(cookie)
        for date in crawl_day_list:
            data_list = []
            data = {}
            res = Obj.szpaas_lowcode_szajax_query_memberoverview(date)
            contents = res.get("content", [])  # list列表
            for content in contents:
                summaryItems = content.get("summaryItems", [])  # list列表
                for summaryItem in summaryItems:
                    data[summaryItem.get("index", "")] = summaryItem.get("value", "")
            data_list.append(data)
            # print(data_list)
            data_list = en_to_cn(data_list, dict_str)  # NOQA
            # print(data_list)

            items = []
            for item in data_list:
                item.update(
                    {
                        "店铺名称": shop_name,
                        "统计日期": date,
                    }
                )
                item["key"] = f"{item['店铺名称']}_{item['统计日期']}"
                items.append(item)

            DBManager(db_config=db_config).update_insert_data(
                items, table_name, primary_key="key"
            )
            logger.info(f"{shop_name}_{date}数据已入库")
        logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")
