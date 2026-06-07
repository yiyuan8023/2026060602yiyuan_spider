from API.API_JingDong.API_Jdsz_Product import JdSzProductAPI
from extra.select_shop_date import select_shop_date
from database import DBManager
from extra.en_to_cn import en_to_cn
from extra.logger_ import logger

# noqa: E501
dict_str = {
    "goodsVisitorNum": "访客数",
    "goodsBrowseNum": "浏览量",
    "goodsConcernNum": "商品关注数",
    "addBuyGoodsPieceNum": "加购商品件数",
    "addBuyCustNum": "加购人数",
    "ordCustNum": "成交客户数",
    "ordNum": "成交单量",
    "ordGoodsPieceNum": "成交商品件数",
    "ordAmt": "成交金额",
    "goodsConverRate": "成交转化率",  # noqa
    "uvValue": "UV价值",
    "shelvesDate": "最近上架时间",
    "spuId": "skuID",  # sku和spu这里也是一样的，但是改了个名字
    "$hasChildren": "是否为商品",
    "ProSkipOut": "详情页跳出率",
    "ExposureNum": "曝光量",
    "ClickNum": "点击次数",
    "ClickRate": "点击率",
    "ForecastSalesNum": "系统预测未来7天销量",
    "OrderCustNum": "下单客户数",
    "OrderGoodsPieceNum": "下单商品件数",
    "OrderAmt": "下单金额",
    "DealToOrderRate": "下单成交转化率",
    "ToOrderRate": "下单转化率",
    "PvRate": "PV现货率",
    "CustPriceAvg": "客单价",
    "UnitPriceAvg": "件单价",
    "proName": "商品名称",
}

if __name__ == "__main__":
    db_config = None  # noqa
    # db_config = "rinnai_py"  # noqa
    shop_name_list = ["BMW官方旗舰店"]  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "jd_jdsz_商品_商品明细_sku_202504"
    site = "京东商智"
    shop_cookies, crawl_day_list = select_shop_date(table_name, site, shop_name_list, 1)

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]
        Obj = JdSzProductAPI(cookie)
        for date in crawl_day_list:

            res = Obj.fetch_product_analysis__product_detail(date, type="1")  # 1代表sku
            gridData_sku = res.get("content", {}).get("gridData", {})  # NOQA
            data = gridData_sku.get("data", [])  # 索引对应的数据
            metaIndex = gridData_sku.get("metaIndex", {})  # 英文标题对应的索引
            results = Obj.title_index_to_data(metaIndex, data)
            # print(results)
            data_list = en_to_cn(results, dict_str)

            items = []
            for item in data_list:
                if item["商品名称"]:
                    item.update(
                        {
                            "店铺名称": shop_name,
                            "统计日期": date,
                        }
                    )
                    item["key"] = (
                        f"{item['店铺名称']}_{item['skuID']}_{item['统计日期']}"
                    )
                    items.append(item)
            # print(items)

            DBManager(db_config=db_config).update_insert_data(
                items, table_name, primary_key="key"
            )
            logger.info(f"{shop_name}_{date}数据已入库")
        logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")
