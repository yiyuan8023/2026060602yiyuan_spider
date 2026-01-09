from API.API_JingDong.API_Jdsz_Product import JdSzProductAPI
from extra.select_shop_date import select_shop_date
from extra.db_manager import DBManager
from extra.en_to_cn import en_to_cn
from extra.logger_ import logger

# noqa: E501
dict_str = {
    "jdr_sch_user_authentication_member_shop_cnt_shopversion_brandmem@date_end&brandmem_card": "有效会员总数", # noqa
    "jdr_sch_user_authentication_member_shop_cnt_shopversion_brandmem_increase@brandmem_card": "有效净增会员数",
    "jdr_sch_user_open_member_shop_cnt_shopversion_brandmem@brandmem_card": "有效新增会员数",
    "jdr_sch_user_invalid_member_shop_cnt_shopversion_brandmem@brandmem_card": "有效解绑会员数",
    "jdr_sch_mkt_brow_shop_cnt_shopversion_brandmem_sz@brandmem_card&browse_brand": "会员进店访客数",
    "jdr_sch_mkt_brow_shop_qtty_shopversion_brandmem_sz@brandmem_card&browse_brand": "会员进店浏览量",
    "jdr_sch_mkt_brow_sku_qtty_shopversion_brandmem_sz@brandmem_card&browse_brand": "商品会员浏览量",
    "jdr_sch_user_follow_sku_sku_qtty_shopversion_brandmem@brandmem_card&follow_brand": "商品会员关注数",
    "jdr_sch_mkt_brow_shop_cnt_shopversion_brandmem_sz@brandmem_card&add_cart": "加购会员数",
    "jdr_sch_mkt_deal_ord_ord_cnt_shopversion_brandmem_sz@brandmem_card": "会员成交客户数",
    "jdr_sch_mkt_deal_ord_ord_dis_qtty_shopversion_brandmem_sz@brandmem_card": "会员成交单量",
    "jdr_sch_mkt_deal_ord_ord_amt_shopversion_brandmem_sz@brandmem_card": "会员成交金额",
    "jdr_sch_mkt_deal_ord_ord_cnt_shopversion_brandmem_sz_ld30_rebuy_brandmem_card": "30天复购会员数", # noqa
    "jdr_sch_mkt_deal_ord_ord_cnt_shopversion_brandmem_sz_brandmem_card_ld30": "30天成交客户", # noqa
    "jdr_sch_mkt_deal_ord_ord_cnt_shopversion_brandmem_sz_rebuy_90d_brandmem_card": "90天复购会员数", # noqa
    "jdr_sch_mkt_deal_ord_ord_cnt_shopversion_brandmem_sz_brandmem_card_90d": "90天成交客户数", # noqa
    "jdr_sch_user_authentication_member_shop_cnt_shopversion_brandmem_client@brandmem_card": "沉寂会员数",

}

if __name__ == '__main__':
    db_config = None  # noqa
    # db_config = "rinnai_py"  # noqa
    shop_name_list = ['BMW官方旗舰店']  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "jd_jdsz_客户_品牌会员_会员概况_开卡会员_202509"
    site = '京东商智'
    shop_cookies, crawl_day_list = select_shop_date(table_name, site, shop_name_list, 1)

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]
        Obj = JdSzProductAPI(cookie)
        for date in crawl_day_list:
            res = Obj.szpaas_lowcode_szajax_query_memberoverview(date)
            print(res)
            body = res.get("body", {})
            print(body)
            data = body.get("data", [])  # 索引对应的数据
            metaIndex = body.get("metaData", {}).get("metaIndex", {})  # 英文标题对应的索引
            results = Obj.title_index_to_data(metaIndex, data)
            print(results)
            data_list = en_to_cn(results, dict_str)  # NOQA

            items = []
            for item in data_list:
                item.update({
                    "店铺名称": shop_name,
                    "统计日期": date,
                })
                item["key"] = f"{item['店铺名称']}_{item['统计日期']}"
                items.append(item)
            # print(items)

            DBManager(db_config=db_config).update_insert_data(items, table_name, primary_key="key")
            logger.info(f"{shop_name}_{date}数据已入库")
    logger.info("-" * 100)
logger.info(f"\n{'*' * 120}")
