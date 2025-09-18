import random
import sys
import re
from time import sleep

from DB import DB
from API_Pdd_Centre import PddDataCentre
from API_Pdd_Analyze import *
from extra import getTimeStr, cus_date, date_day
from email_ import send_email
from settings import accout_name, MIN_WAIT_TIME, MAX_WAIT_TIME
from log import logger, error_logs, error_logs2


def crawl_service_data__after_sales_data(query_data):
    """
    pdd_数据中心_服务数据_售后数据 入口
    数据拼装，翻页
    :param queryDate:
    :param date_type:
    :return:
    """
    logger.info(f"正在爬取’{shop_name}‘店铺’{queryDate}‘的’pdd_数据中心_服务数据_售后数据‘数据")
    res_json = pdd.service_data__after_sales_data(query_data)
    if "会话已过期" == res_json.get("error_msg", None):
        logger.error(f"’{shop_name}‘的店铺cookie为空或者已失效({cc_email})")
        cc_emails.append(cc_email)
        pdd.cookie = None
    else:
        result = service_data__after_sales_data__analyze(res_json)
        if result:
            result[0]["item"].update({
                "统计日期": queryDate,
                "唯一去重": f"{pdd.shop_name}{queryDate}",
                "店铺名称": pdd.shop_name

            })
            cus_db.do_insert(result)


def crawl_trade_data__data_overview(queryDate, date_type="day"):
    """
    pdd_数据中心_交易数据_数据总览 入口
    数据拼装，翻页
    :param queryDate:
    :param date_type:
    :return:
    """

    if date_type == "day":
        logger.info(f"正在爬取’{shop_name}‘店铺’{queryDate}‘的’数据中心_交易数据_数据总览‘数据，类型’{date_type}‘")
        res_json, font_dict = pdd.trade_data__data_overview(queryDate, queryType=7)
        if "会话已过期" == res_json.get("error_msg", None):
            logger.error(f"’{shop_name}‘的店铺cookie为空或者已失效({cc_email})")
            cc_emails.append(cc_email)
            pdd.cookie = None
        else:
            result = trade_data__data_overview__analyze(res_json, font_dict)
            if result:
                result[0]["item"].update({
                    "统计时间": queryDate,
                    "唯一去重": f"{queryDate}{pdd.shop_name}",
                    "店铺名称": pdd.shop_name,
                    "日期类型": "day"

                })
                cus_db.do_insert(result)
    elif date_type == "month":
        logger.info(
            f"正在爬取’{shop_name}‘店铺’{queryDate}‘的上个月’pdd_数据中心_交易数据_数据总览‘数据，类型’{date_type}‘")
        tt = cus_date()
        queryDate = tt["ToDate"]
        res_json, font_dict = pdd.trade_data__data_overview(queryDate, queryType=4)
        print(res_json)
        if "会话已过期" == res_json.get("error_msg", None):
            logger.error(f"’{shop_name}‘的店铺cookie为空或者已失效({cc_email})")
            cc_emails.append(cc_email)
            pdd.cookie = None
        else:
            result = trade_data__data_overview__analyze(res_json, font_dict)
            if result:
                result[0]["item"].update({
                    "统计时间": f"{tt['FormDate']} 至 {tt['ToDate']}",
                    "唯一去重": f"{tt['FormDate']} 至 {tt['ToDate']}{pdd.shop_name}",
                    "店铺名称": pdd.shop_name,
                    "日期类型": "month"

                })
                cus_db.do_insert(result)


def crawl_flow_data__flow_board(begin_date, end_data):
    """
    pdd_数据中心_流量数据 入口
    数据拼装，翻页
    :param queryDate:
    :param date_type:
    :return:
    """
    if begin_date == end_data:
        queryDate = begin_date
    else:
        queryDate = f"{begin_date}~{end_data}"
    logger.info(f"正在爬取’{shop_name}‘店铺’{queryDate}‘的’pdd_数据中心_流量数据‘数据")
    res_json = pdd.flow_data__flow_board(begin_date, end_data)
    if "会话已过期" == res_json.get("error_msg", None):
        logger.error(f"’{shop_name}‘的店铺cookie为空或者已失效({cc_email})")
        cc_emails.append(cc_email)
        pdd.cookie = None
    else:
        result = flow_data__flow_board__analyze(res_json)
        if result:
            result[0]["item"].update({
                "统计时间": queryDate,
                "唯一去重": f"{queryDate}{pdd.shop_name}",
                "店铺名称": pdd.shop_name

            })
            cus_db.do_insert(result)


def crawl_goods_data__goods_detail(startDate, endDate, pageNum=1):
    """
    pdd_数据中心_商品数据_商品明细_商品明细效果 入口
    数据拼装，翻页
    :param queryDate:
    :param date_type:
    :return:
    """
    if startDate == endDate:
        queryDate = endDate
    else:
        queryDate = f"{startDate}~{endDate}"
    logger.info(f"正在爬取’{shop_name}‘店铺’{queryDate}‘的’pdd_数据中心_商品数据_商品明细_商品明细效果‘数据")
    res_json, font_dict = pdd.goods_data__goods_detail(startDate, endDate, pageNum)
    if "会话已过期" == res_json.get("error_msg", None):
        logger.error(f"’{shop_name}‘的店铺cookie为空或者已失效({cc_email})")
        cc_emails.append(cc_email)
        pdd.cookie = None
    else:
        totalNum = res_json["result"].get("totalNum", 0)
        if totalNum != 0:
            result = goods_data__goods_detail__analyze(res_json, font_dict)
            if result:
                for i in result[0]["item"]:
                    i.update({
                        "统计日期": queryDate,
                        "唯一去重": f"{i['商品信息']}{i['商品ID']}{queryDate}",
                        "店铺名称": pdd.shop_name

                    })
                cus_db.do_insert(result[0:2])
            if pageNum * 50 < totalNum:
                pageNum += 1
                crawl_goods_data__goods_detail(startDate, endDate, pageNum)


def crawl_goods_data__goods_general_situation(queryDate):
    """
    pdd_数据中心_商品数据_商品概况 入口
    数据拼装，翻页
    :param queryDate:
    :param date_type:
    :return:
    """
    logger.info(f"正在爬取’{shop_name}‘店铺’{queryDate}‘的’pdd_数据中心_商品数据_商品概况‘数据")
    res_json, font_dict = pdd.goods_data__goods_general_situation(queryDate)

    if "会话已过期" == res_json.get("error_msg", None):
        logger.error(f"’{shop_name}‘的店铺cookie为空或者已失效({cc_email})")
        cc_emails.append(cc_email)
        pdd.cookie = None
    else:
        result = goods_data__goods_general_situation__analyze(res_json, font_dict)
        if result:
            result[0]["item"].update({
                "统计日期": queryDate,
                "primekey": f"{pdd.shop_name}{queryDate}",
                "店铺名称": pdd.shop_name

            })
            cus_db.do_insert(result)
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
            if shop_name:
                cc_email = i[2]
                # 实例化一个pdd对象
                pdd = PddDataCentre(cookie=cookie, shop_name=shop_name)
                # 默认滚动采集【近3天】数据
                for j in range(1, 3+1):
                    # 获取前一天的时间
                    queryDate = getTimeStr(-j)
                    # 爬取 pdd_数据中心_交易数据_数据总览
                    if pdd.cookie:
                        sleep(random.uniform(MIN_WAIT_TIME, MAX_WAIT_TIME))
                        crawl_trade_data__data_overview(queryDate, date_type="day")
                    else:
                        break
                    # 爬取 pdd_数据中心_服务数据_售后数据
                    if pdd.cookie:
                        sleep(random.uniform(MIN_WAIT_TIME, MAX_WAIT_TIME))
                        crawl_service_data__after_sales_data(queryDate)
                    else:
                        break
                    # # 爬取 pdd_数据中心_流量数据
                    # if pdd.cookie:
                    #     sleep(random.uniform(MIN_WAIT_TIME, MAX_WAIT_TIME))
                    #     crawl_flow_data__flow_board(queryDate, queryDate)
                    # else:
                    #     break
                    # 爬取 pdd_数据中心_商品数据_商品明细_商品明细效果
                    # if pdd.cookie:
                    #     sleep(random.uniform(MIN_WAIT_TIME, MAX_WAIT_TIME))
                    #     crawl_goods_data__goods_detail(queryDate, queryDate)
                    # else:
                    #     break
                    # 爬取 pdd_数据中心_商品数据_商品概况
                    # if pdd.cookie:
                    #     sleep(random.uniform(MIN_WAIT_TIME, MAX_WAIT_TIME))
                    #     crawl_goods_data__goods_general_situation(queryDate)
                    # else:
                    #     break
                    # 每月二号爬取 pdd_数据中心_交易数据_数据总览 月份数据
                    # now_day = date_day()
                    # if now_day == 10 and pdd.cookie:
                    #     sleep(random.uniform(MIN_WAIT_TIME, MAX_WAIT_TIME))
                    #     crawl_trade_data__data_overview(queryDate, date_type="month")
                    # elif not pdd.cookie:
                    #     break
                    # else:
                    #     continue

    # 将错误信息汇总
    if error_logs:
        body = "".join(error_logs)
        send_email(f"PDD报错信息_{getTimeStr()}", body)
    if error_logs2:
        error_logs2_html = []
        for i in error_logs2:
            modified_str = ""
            pattern = r'\{.*?\}'
            email_pattern = r'\b[\w.-]+@[\w.-]+\.\w+\b'
            # 使用re.sub进行替换，将匹配到的内容包裹在指定的HTML标签中
            modified_str = re.sub(pattern,
                                  r'<span style="color:red; font-weight:bold;white-space: nowrap;">\g<0></span>', i)
            # print(modified_str)
            pattern = r'’([^‘]+)‘的店铺cookie为空或者已失效\(([\w.-]+@[\w.-]+\.\w+)\)'
            #     # 使用re.sub进行替换，利用捕获组(\g<1>, \g<2>)引用原匹配内容
            modified_str = re.sub(pattern,
                                  r'<span style="color:red; font-weight:bold;white-space: nowrap;">\g<1></span> 的店铺cookie为空或者已失效(<span style="color:red; font-weight:bold;white-space: nowrap;">\g<2></span>)',
                                  modified_str)
            error_logs2_html.append(f'<p>{modified_str}</p>')
        body2 = "".join(error_logs2_html)
        send_email(f"PDD报错信息_{getTimeStr()}", body2, cc_emails, content_type="html")
