# -*- coding: utf-8 -*-
# @Time : 2024/9/25 10:12
# @Author : Shao0000
# @Email : Shao0000@aliyun.com
# @File : script.py
# @Project : JDSZ
import random
from time import sleep

from DB import DB
from JdSzCustomAPI import JdSzCustomAPI
from API_Jdsz_Product import JdSzProductAPI
from API_Jdsz_ReportAPI import JdSzReportAPI
from JdSzServiceAPI import JdSzServiceAPI
from cn_en_map import cn_en_map
from JdSzTradeAPI import JdSzTradeAPI
from extra import generate_dates, get_1970_days, format_date
from log_ import logger
from settings_pass import WAIT_TIME_MAX, WAIT_TIME_MIN

db = DB()


def spider_cn(script, content):
    item = {}
    for k, v in cn_en_map[script].items():
        item[k] = content.get(v[0], {}).get(v[1])
    return item


def flatten_data(data):
    """
    展平数据结构，包括子节点。
    """
    result = []
    for item in data:
        result.append(item)
        result.extend(flatten_data(item.get("children", [])))
    return result


def spider_9_cn(i):
    item = {}
    for k, v in cn_en_map["jd1_1_09_jdsz"].items():

        if isinstance(v, tuple):
            if i[v[1]] == "999999":
                item[k] = i[v[0]]
            else:
                item[k] = f"{i[v[0]]}--{i[v[1]]}"
        else:
            item[k] = i[v]
    return item


def spider_2_6_cn(gridData, d, shop_name, script):
    data = gridData["data"]
    metaIndex = gridData["metaIndex"]
    items = []
    for i in data:
        item = {}
        for k, v in cn_en_map[script].items():
            item[k] = i[metaIndex[v]]

        item.update(
            {
                "统计日期": d,
                "日期类型": "day",
                "店铺名称": shop_name,
                "唯一去重": (
                    f"{get_1970_days(d)}{item['商品ID']}{shop_name}"
                    if script == "jd1_1_02_jdsz"
                    else f"{get_1970_days(d)}{item['skuID']}{shop_name}"
                ),
            }
        )
        if isinstance(item["是否为商品"], bool) and (
            (item["是否为商品"] and script == "jd1_1_02_jdsz")
            or (not item["是否为商品"] and script == "jd1_1_06_jdsz")
        ):
            item["是否为商品"] = str(item["是否为商品"])
            items.append(item)
    return items


def spider_4_cn(res_json, script):
    data = {}
    content = res_json["content"]
    for i in content:
        code = i["code"]
        data[code] = {}
        for j in i["summaryItems"]:
            data[code][j["index"]] = j
    item = {}
    for k, v in cn_en_map[script].items():
        item[k] = data[v[0]][v[1]][v[2]]
    return item


def spider_5_cn(res_json, script, d, shop_name):
    data = res_json["body"]["data"]
    metaIndex = res_json["body"]["metaData"]["metaIndex"]
    items = []
    for i in data:
        item = {}
        for k, v in cn_en_map[script].items():
            if isinstance(v, str):
                item[k] = i[metaIndex[v]]
            else:
                math_list = []
                for j in v:
                    if j in metaIndex.keys():
                        math_list.append(float(i[metaIndex[j]]))
                    else:
                        math_list.append(j)

                s = eval("".join(map(str, math_list)))
                item[k] = s
        item.update(
            {
                "统计日期": d,
                "日期类型": "day",
                "店铺名称": shop_name,
                "唯一去重": f"{d.replace('-','')},{shop_name}",
            }
        )
        items.append(item)
    return items


def jd1_1_01_jdsz(**kwargs):
    cookie = kwargs.get("cookie")
    shop_name = kwargs.get("shop_name")
    account_name = kwargs.get("account_name")
    startDate = kwargs.get("startDate")
    endDate = kwargs.get("endDate")
    # date_ = kwargs.get("date_")
    JdSzTrade = JdSzTradeAPI(
        cookie=cookie, shop_name=shop_name, account_name=account_name
    )
    date_list = generate_dates(startDate, endDate)
    for d in date_list:
        sleep(random.uniform(WAIT_TIME_MIN, WAIT_TIME_MAX))
        logger.info(
            f"正在爬取”{shop_name}“ {d} 的 ”jd1_1_01_jdsz_交易_交易概况_全部渠道【商家版】“"
        )
        res_json = JdSzTrade.fetch_trade_summary(date=d, startDate=d, endDate=d)
        # print(res_json)
        content = res_json["content"]
        item = spider_cn("jd1_1_01_jdsz", content)
        item.update(
            {
                "店铺名称": shop_name,
                "统计日期": d,
                "日期类型": "day",
                "唯一去重": f"{shop_name}{get_1970_days(d)}",
            }
        )
        db.do_insert(item, "jd_jdsz_交易_交易概况_全部渠道")


def jd1_1_09_jdsz(**kwargs):
    cookie = kwargs.get("cookie")
    shop_name = kwargs.get("shop_name")
    account_name = kwargs.get("account_name")
    startDate = kwargs.get("startDate")
    endDate = kwargs.get("endDate")
    JdSzProduct = JdSzProductAPI(
        cookie=cookie, shop_name=shop_name, account_name=account_name
    )
    date_list = generate_dates(startDate, endDate)
    for d in date_list:
        sleep(random.uniform(WAIT_TIME_MIN, WAIT_TIME_MAX))
        logger.info(
            f"正在爬取”{shop_name}“ {d} 的 ”jd1_1_09_jdsz_商品_类目分析_行业类目【商家版】“"
        )
        res_json = JdSzProduct.fetch_product_analysis__category_analysis(
            date=d, startDate=d, endDate=d
        )
        # print(res_json)
        data = res_json["body"]["data"]
        if data:
            data = flatten_data(data)
            items = []
            for i in data:
                item = spider_9_cn(i)
                item.update(
                    {
                        "店铺名称": shop_name,
                        "日期范围": f"{d}|{d}",
                        "统计日期": d,
                        "日期类型": "day",
                        "key": f"{shop_name}|{item['行业类目']}|{d}|day",
                    }
                )
                items.append(item)
            db.do_insert(items, "jd_jdsz_商品_类目分析_行业类目")
        else:
            logger.warning(
                f"”{shop_name}“ {d} 的 ”jd1_1_09_jdsz_商品_类目分析_行业类目【商家版】“ 无数据"
            )


def jd1_1_07_jdsz(**kwargs):
    cookie = kwargs.get("cookie")
    shop_name = kwargs.get("shop_name")
    account_name = kwargs.get("account_name")
    startDate = kwargs.get("startDate")
    endDate = kwargs.get("endDate")
    JdSzService = JdSzServiceAPI(
        cookie=cookie, shop_name=shop_name, account_name=account_name
    )
    date_list = generate_dates(startDate, endDate)
    for d in date_list:
        sleep(random.uniform(WAIT_TIME_MIN, WAIT_TIME_MAX))
        logger.info(
            f"正在爬取”{shop_name}“ {d} 的 ”jd1_1_07_jdsz_服务_服务分析_售后服务单量【商家版】“"
        )
        res_json = JdSzService.fetch_service_analysis__after_sale_service(
            date=d, startDate=d, endDate=d
        )
        summary = res_json["content"]["summary"]
        item = spider_cn("jd1_1_07_jdsz", summary)
        item.update(
            {
                "店铺名称": shop_name,
                "统计日期": d,
                "日期类型": "day",
                "唯一去重": f"{shop_name},{d.replace('-', '')}",
            }
        )
        db.do_insert(item, "jd_jdsz_服务_服务分析_售后服务单量")


def jd1_1_02_jdsz(**kwargs):
    cookie = kwargs.get("cookie")
    shop_name = kwargs.get("shop_name")
    account_name = kwargs.get("account_name")
    startDate = kwargs.get("startDate")
    endDate = kwargs.get("endDate")
    JdSzProduct = JdSzProductAPI(
        cookie=cookie, shop_name=shop_name, account_name=account_name
    )
    date_list = generate_dates(startDate, endDate)
    for d in date_list:
        sleep(random.uniform(WAIT_TIME_MIN, WAIT_TIME_MAX))
        logger.info(
            f"正在爬取”{shop_name}“ {d} 的 ”jd1_1_02_jdsz_商品_商品明细_spu【商家版】“"
        )
        res_json = JdSzProduct.fetch_product_analysis__product_detail(
            date=d, startDate=d, endDate=d
        )
        gridData = res_json["content"]["gridData"]
        items = spider_2_6_cn(gridData, d, shop_name, "jd1_1_02_jdsz")
        # print(items)
        db.do_insert(items, "jd_jdsz_商品_商品明细_spu")


def jd1_1_06_jdsz(**kwargs):
    cookie = kwargs.get("cookie")
    shop_name = kwargs.get("shop_name")
    account_name = kwargs.get("account_name")
    startDate = kwargs.get("startDate")
    endDate = kwargs.get("endDate")
    JdSzProduct = JdSzProductAPI(
        cookie=cookie, shop_name=shop_name, account_name=account_name
    )
    date_list = generate_dates(startDate, endDate)
    for d in date_list:
        sleep(random.uniform(WAIT_TIME_MIN, WAIT_TIME_MAX))
        logger.info(
            f"正在爬取”{shop_name}“ {d} 的 ”jd1_1_06_jdsz_商品_商品明细_sku【商家版】“"
        )
        res_json = JdSzProduct.fetch_product_analysis__product_detail(
            date=d, startDate=d, endDate=d, type="1"
        )
        gridData = res_json["content"]["gridData"]
        items = spider_2_6_cn(gridData, d, shop_name, "jd1_1_06_jdsz")
        # print(items)
        db.do_insert(items, "jd_jdsz_商品_商品明细_sku")


def jd1_1_08_jdsz(**kwargs):
    cookie = kwargs.get("cookie")
    shop_name = kwargs.get("shop_name")
    account_name = kwargs.get("account_name")
    startDate = kwargs.get("startDate")
    endDate = kwargs.get("endDate")
    JdSzReport = JdSzReportAPI(
        cookie=cookie, shop_name=shop_name, account_name=account_name
    )
    sleep(random.uniform(WAIT_TIME_MIN, WAIT_TIME_MAX))
    logger.info(
        f"正在爬取”{shop_name}“ {startDate}-{endDate} 的 ”jd1_1_08_jdsz_报表_新建报表_店铺【商家版】“"
    )
    df = JdSzReport.fetch_report_analysis__my_report__excel(
        startDate=startDate, endDate=endDate
    )
    if df.empty:
        items = {}
    else:
        items = df.to_dict("records")
    for i in items:
        i.update(
            {
                "统计日期": format_date(i["日期"]),
                "店铺名称": shop_name,
                "日期类型": "day",
                "唯一去重": f"{shop_name}{i['日期']}day",
            }
        )
    # print(items)
    db.do_insert(items, "jd_jdsz_报表_新建报表_店铺")


def jd1_1_04_jdsz(**kwargs):
    cookie = kwargs.get("cookie")
    shop_name = kwargs.get("shop_name")
    account_name = kwargs.get("account_name")
    startDate = kwargs.get("startDate")
    endDate = kwargs.get("endDate")
    JdSzCustom = JdSzCustomAPI(
        cookie=cookie, shop_name=shop_name, account_name=account_name
    )
    date_list = generate_dates(startDate, endDate)
    for d in date_list:
        sleep(random.uniform(WAIT_TIME_MIN, WAIT_TIME_MAX))
        logger.info(
            f"正在爬取”{shop_name}“ {d} 的 ”jd1_1_04_jdsz_客户_关注店铺用户概况_数据概览【商家版】“"
        )
        res_json = JdSzCustom.fetch_fans_summary__data_summary(
            date=d, startDate=d, endDate=d
        )
        item = spider_4_cn(res_json, "jd1_1_04_jdsz")
        item.update(
            {
                "店铺名称": shop_name,
                "统计日期": d,
                "日期类型": "day",
                "唯一去重": f"{d}|{shop_name}|day",
            }
        )
        db.do_insert(item, "jd_jdsz_客户_关注店铺用户概况_数据概览")


def jd1_1_05_jdsz(**kwargs):
    cookie = kwargs.get("cookie")
    shop_name = kwargs.get("shop_name")
    account_name = kwargs.get("account_name")
    startDate = kwargs.get("startDate")
    endDate = kwargs.get("endDate")
    JdSzCustom = JdSzCustomAPI(
        cookie=cookie, shop_name=shop_name, account_name=account_name
    )
    date_list = generate_dates(startDate, endDate)
    for d in date_list:
        sleep(random.uniform(WAIT_TIME_MIN, WAIT_TIME_MAX))
        logger.info(
            f"正在爬取”{shop_name}“ {d} 的 ”jd1_1_05_jdsz_客户_品牌会员_会员概况_开卡会员【商家版】“"
        )
        res_json = JdSzCustom.fetch_vip_summary__data_summary(
            date=d, startDate=d, endDate=d
        )
        items = spider_5_cn(res_json, "jd1_1_05_jdsz", d, shop_name)
        db.do_insert(items, "jd_jdsz_客户_品牌会员_会员概况_开卡会员_new")
