import sys

from DB import DB
from API_Pdd_Centre import PddDataCentre
from API_Pdd_Analyze import *
from extra import getTimeStr, cus_date, date_day
from email_ import send_email
from settings import accout_name
from log import logger, error_logs, error_logs2

def crawl_goods_data__goods_general_situation_realtime():
    """
    pdd_数据中心_商品数据_商品概况 入口 实时数据
    数据拼装，翻页
    :param queryDate:
    :param date_type:
    :return:
    """
    logger.info(f"正在爬取’{shop_name}‘店铺的’pdd_数据中心_商品数据_商品概况‘实时数据")
    res_json = pdd.goods_data__goods_general_situation_realtime()

    if "会话已过期" == res_json.get("error_msg", None):
        logger.error(f"’{shop_name}‘的店铺cookie为空或者已失效({cc_email})")
        cc_emails.append(cc_email)
        pdd.cookie = None
    else:
        result = goods_data__goods_general_situation_realtime__analyze(res_json)
        if result:
            result[1]["item"].update({
                "shop_name": pdd.shop_name

            })
            cus_db.do_insert(result)


if __name__ == '__main__':
    print(sys.argv)
    shop_name_str = sys.argv[1] if len(sys.argv) > 1 else None

    # # 实例化DB
    cus_db = DB()
    cc_emails = []
    #
    # # 查询账号对应的店铺名和cookie
    res = cus_db.do_select(shop_name_str)
    if res:
        for i in res:
            cookie = i[1]
            shop_name = i[0]
            cc_email = i[2]
            # 实例化一个pdd对象
            pdd = PddDataCentre(cookie=cookie, shop_name=shop_name)
            # 爬取 pdd_数据中心_商品数据_商品概况
            if pdd.cookie:
                crawl_goods_data__goods_general_situation_realtime()
            else:
                break


    # 将错误信息汇总
    if error_logs:
        body = "".join(error_logs)
        send_email(f"PDD实时报错信息_{getTimeStr()}", body)
    if error_logs2:
        body2 = "".join(error_logs2)
        send_email(f"PDD实时报错信息_{getTimeStr()}", body2, cc_emails)
