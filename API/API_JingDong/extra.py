# -*- coding: utf-8 -*-
# @Time : 2024/9/23 11:12
# @Author : Shao0000
# @Email : Shao0000@aliyun.com
# @File : extra.py
# @Project : JDSZ
from copy import deepcopy
from datetime import datetime, timedelta

import requests
import json

from settings_pass import SCRIPT_SET


def getTimeStr(timedelta_: int = 0) -> str:
    """
    获取当前时间日期的前n天或者后n天日期的字符串形式
    默认获取当天的时间"2024-3-21"
    :param timedelta_:
    :return:
    """
    # 获取今天的日期
    today = datetime.now()
    time_ = today + timedelta(days=timedelta_)
    time_str = time_.strftime("%Y-%m-%d")
    return time_str


def cookie_jar_to_cookie_str(cookie_jar):
    """
    cookie_jar转cookie_str
    :param cookie_jar:
    :return:
    """
    d = []
    for i in cookie_jar:
        d.append(f"{i['name']}={i['value']}")
    cookie_str = "; ".join(d)
    return cookie_str


def generate_dates(start_date_str, end_date_str):
    # 将字符串转换为日期对象
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    # 初始化一个空列表来存储日期
    dates = []

    # 当前日期初始化为开始日期
    current_date = start_date

    # 循环直到当前日期超过结束日期
    while current_date <= end_date:
        # 添加当前日期到列表中
        dates.append(current_date.strftime("%Y-%m-%d"))
        # 增加一天
        current_date += timedelta(days=1)

    return dates


def spider_res(res_json):
    """
    处理bihome返回的res
    :param res_json:
    :return:
    """
    result = []
    data = res_json["data"]
    for i in data:
        if i["requirement_status"] == "在运营":
            cookie_ori = i["cookie"]
            cookie_jar = json.loads(cookie_ori)["cookies"]
            cookie_str = cookie_jar_to_cookie_str(cookie_jar)
            d = deepcopy(i)
            d["cookie"] = cookie_str
            result.append(d)
    all_shop_name = [i["shop_name"] for i in result]
    return all_shop_name, result


def get_bihome_requirements():
    """
    获取JDSZ下面的所有脚本需要执行的店铺以及cookie
    :return:
    """
    url = "http://192.168.10.223:5000/bihome_requirements"

    payload = json.dumps(
        {
            "field": [
                "shop_name",
                "account_name",
                "cookie",
                "requirement_status",
            ],
            "requirement_names": list(SCRIPT_SET),
        }
    )
    headers = {
        "User-Agent": "Apifox/1.0.0 (https://apifox.com)",
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Host": "192.168.10.223:5000",
        "Connection": "keep-alive",
    }

    res = requests.request("POST", url, headers=headers, data=payload)
    res_json = res.json()
    return spider_res(res_json)


def get_1970_days(t: str, date_format="%Y-%m-%d"):
    from datetime import datetime

    """
    同excel
    """
    # 解析时间字符串为datetime对象
    parsed_datetime = datetime.strptime(t, date_format)

    # 创建1970年1月1日的datetime对象
    epoch_datetime = datetime(1900, 1, 1)

    # 计算时间差
    delta = parsed_datetime - epoch_datetime

    # 提取天数
    # 加2 是因为 excel 把1900-2月 算成29tian 瑞年
    days_since_epoch = delta.days + 2
    return days_since_epoch


def format_date(input_date):
    """
    将形如 '20240901' 的日期字符串转换为 '2024-09-01' 格式。

    :param input_date: 形如 '20240901' 的字符串
    :return: 形如 '2024-09-01' 的字符串
    """
    try:
        # 尝试将输入字符串解析为日期对象
        date_obj = datetime.strptime(str(input_date), "%Y%m%d")
    except ValueError:
        # 如果输入格式错误，抛出异常
        raise ValueError("Input date must be an 8-digit string in the format YYYYMMDD.")

    # 将日期对象转换为 'YYYY-MM-DD' 格式的字符串
    formatted_date = date_obj.strftime("%Y-%m-%d")

    return formatted_date
