from API.API_JingDong.API_Jdsz_Product import JdSzProductAPI
from extra.select_shop_date import select_shop_date
from extra.db_manager import DBManager
from extra.en_to_cn import en_to_cn
from extra.logger_ import logger

# noqa: E501
dict_str = {
    "NumChange": "换货量",
    "THRate": "退货率(出库)",
    # 'OrdDisRatio': None,
    "NumFix": "返修量",
    # 'ShopActScore': 0.0,
    "Duration": "售后服务时长",
    "NumTH": "申请退货件数",
    "AmtTH": "服务单退款金额",
    "OrdDisOther": "交易纠纷",
}

if __name__ == "__main__":
    db_config = None  # noqa
    # db_config = "rinnai_py"  # noqa
    shop_name_list = ["BMW官方旗舰店"]  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "jd_jdsz_服务_服务分析_售后服务单量"
    site = "京东商智"
    shop_cookies, crawl_day_list = select_shop_date(table_name, site, shop_name_list, 1)

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]
        data_list = []
        Obj = JdSzProductAPI(cookie)
        for date in crawl_day_list:
            data = {}
            res = Obj.fetch_service_analysis__after_sale_service(date)

            content = res.get("content", {}).get("summary", {})
            for K, V in content.items():
                data[K] = V.get("value", None)
            # print(data)
            data_list.append(data)
            data_list = en_to_cn(data_list, dict_str)
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
