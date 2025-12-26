# File: pdd_数据中心_服务数据_售后数据

from API.API_Pdd.API_Pdd_Centre import PddDataCentre
from API.API_Pdd.API_Pdd_Font_Decrypt import decrypt_unicode_string, res_decrypt
from extra.select_shop_date import select_shop_date
from extra.db_manager import DBManager
from extra.logger_ import logger
from extra.settings import EMAIL

# noqa: E501
dict_str = {'statDate': '统计日期',
            'goodsId': '商品id',
            'goodsName': '商品标题',
            'goodsFavCnt': '商品收藏用户数',
            'goodsUv': '商品访客数',
            'goodsPv': '商品浏览量',
            'payOrdrCnt': '成交件数',
            'goodsVcr': '成交转化率',
            'ordrVstrRto': '下单率',  # noqa
            'payOrdrGoodsQty': '成交订单数',
            'payOrdrUsrCnt': '成交买家数',
            'payOrdrAmt': '成交金额',
            'imprUsrCnt': '流量损失指数',  # noqa
            }

if __name__ == '__main__':
    db_config = None  # noqa
    cc_email = EMAIL
    # db_config = "rinnai_py"  # noqa
    shop_name_list = ['林内官方旗舰店']  # 默认采集店铺,如果为[],则采集所有店铺
    table_name = "pdd_数据中心_商品数据_商品明细_商品明细效果"
    site = '拼多多'
    shop_cookies, crawl_day_list = select_shop_date(table_name, site, shop_name_list, 1)

    for i in shop_cookies:
        cookie = i[1]
        shop_name = i[0]

        Obj = PddDataCentre(cookie)
        for date in crawl_day_list:
            items = []
            cc_emails = []
            res, font_dict = Obj.goods_data__goods_detail(date, date)
            if "会话已过期" == res.get("error_msg", None):
                logger.error(f"’{shop_name}‘的店铺cookie为空或者已失效({cc_email})")
                cc_emails.append(cc_email)
                # pdd.cookie = None
            else:

                res_data_list = res.get("result", {}).get("goodsDetailList", [])  # 原始数据
                res_items = res_decrypt(res_data_list, font_dict, dict_str)  # 数据解密,修改中文字段，同步进行

                for item in res_items:
                    item.update({
                        "店铺名称": shop_name,
                    })
                    item["key"] = f"{item['店铺名称']}_{item['商品id']}_{item['统计日期']}"  #
                    items.append(item)

                print(items)

                DBManager(db_config=db_config).update_insert_date(items, table_name, primary_key="key")
                logger.info(f"{shop_name}_{crawl_day_list}数据已入库")
        logger.info("-" * 100)
logger.info(f"\n{'*' * 120}")
