# -*- coding: utf-8 -*-
# @Time : 2024/9/23 10:49
# @Author : Shao0000
# @Email : Shao0000@aliyun.com
# @File : Start.py
# @Project : JDSZ
import time
from copy import deepcopy

import requests

from API_Jdsz_Base import CookieFailError
from email_ import send_email, str_html
from script import *
from extra import get_bihome_requirements, getTimeStr
import argparse
from log_ import logger, error_logs, error_logs2
from settings_pass import (
    SCRIPT_SET,
    JDSZ_API_SCRIPT_MAP,
    START_DATE_DAYS,
    END_DATE_DAYS,
)

# 获取登记的所有要执行的店铺及脚本
valid_shop_names, plan_execute_list = get_bihome_requirements()
valid_programs = SCRIPT_SET


def requirement_names_list__dict(requirement_names):
    d = {}
    for i in requirement_names:
        api = JDSZ_API_SCRIPT_MAP[i][0]
        if api not in d.keys():
            d[api] = [i]
        else:
            d[api].append(i)
    return d


def filter_execute_list(execute_list, shop_name, program):
    """
    把解析到的命令行参数和允许的最大范围的店铺及脚本进行筛选
    :param execute_list:
    :param shop_name:
    :param program:
    :return:
    """
    result = []
    if (not shop_name) and (not program):
        result = plan_execute_list
    else:
        if (not program) and shop_name:
            for i in execute_list:
                if i["shop_name"] in shop_name:
                    result.append(i)
                else:
                    logger.error(f"【{i.get('shop_name')}】不在BIHome执行清单内")
        else:
            islogger = True
            if (not shop_name) and program:
                shop_name = valid_shop_names
                islogger = False
            for i in execute_list:
                j = deepcopy(i)
                if i.get("shop_name") not in shop_name:
                    pass
                else:
                    requirement_names = i.get("requirement_names", [])
                    req_list = list(set(requirement_names) & set(program))
                    if req_list:
                        j["requirement_names"] = req_list
                        result.append(j)
                        if set(req_list) != set(program):
                            if islogger:
                                logger.error(
                                    f"【{i.get('shop_name')}】的BIHome执行清单内没有脚本：{list(set(program) - set(req_list))}"
                                )
                    else:
                        if islogger:
                            logger.error(
                                f"【{i.get('shop_name')}】的BIHome执行清单内没有脚本：{program}"
                            )

    return result


def valid_shop_name(shop_name):
    # 定义有效的店铺选项
    if shop_name not in valid_shop_names:
        raise argparse.ArgumentTypeError("%s 不是一个有效的店铺" % shop_name)
    return shop_name


def valid_program(program):
    # 定义有效的脚本选项

    if program not in valid_programs:
        raise argparse.ArgumentTypeError("%s 不是一个有效的脚本" % program)
    return program


if __name__ == "__main__":

    # 解析命令行参数

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        "--shop_name",
        help="店铺名称(多个店铺用空格隔开)",
        required=False,
        type=valid_shop_name,
        choices=valid_shop_names,
        nargs="+",
    )
    parser.add_argument(
        "-p",
        "--program",
        help="脚本名称(多个脚本用空格隔开)",
        required=False,
        type=valid_program,
        choices=valid_programs,
        nargs="+",
    )
    parser.add_argument(
        "-start",
        "--start_date",
        help="开始时间（xxxx-xx-xx）",
        required=False,
        type=str,
        default=getTimeStr(START_DATE_DAYS),
    )
    parser.add_argument(
        "-end",
        "--end_date",
        help="开始时间（xxxx-xx-xx）",
        required=False,
        type=str,
        default=getTimeStr(END_DATE_DAYS),
    )
    parser.add_argument(
        "-date",
        "--date",
        help="某一天时间（xxxx-xx-xx），且这个时间参数的优先级最高",
        required=False,
        type=str,
    )
    args = parser.parse_args()
    date_ = args.date
    if date_:
        startDate = date_
        endDate = date_
    else:
        startDate = args.start_date
        endDate = args.end_date
    # 获取执行的清单
    execute_list = filter_execute_list(plan_execute_list, args.shop_name, args.program)
    print(execute_list)
    for i in execute_list:
        requirement_names = i["requirement_names"]
        print(f"#{i['shop_name']}#{requirement_names}")
        k = {
            "shop_name": i["shop_name"],
            "cookie": i["cookie"],
            "startDate": startDate,
            "endDate": endDate,
            # "date_":date_,
            "account_name": i["account_name"],
        }
        for requirement_name in requirement_names:

            try:
                print(f"####{requirement_name}")
                eval(f"{requirement_name}(**k)")
            except CookieFailError as e:
                break
            except Exception as e:
                logger.error(e)
        # 将错误信息汇总

    # # 刷新链对应关系
    # f5_dict = {
    #     "jd_jdsz_商品_商品明细_spu": "https://bi.bi-cheng.cn/public-api/data-source/jc0db2bc8be944456b01cf21/refresh?token=j861edcf6df5549b78bf903d",
    # }

    # headers = {
    #     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    #     "Accept-Language": "zh-CN,zh;q=0.9",
    #     "Cache-Control": "max-age=0",
    #     "Connection": "keep-alive",
    #     "Sec-Fetch-Dest": "document",
    #     "Sec-Fetch-Mode": "navigate",
    #     "Sec-Fetch-Site": "none",
    #     "Sec-Fetch-User": "?1",
    #     "Upgrade-Insecure-Requests": "1",
    #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
    #     "sec-ch-ua": "\"Google Chrome\";v=\"107\", \"Chromium\";v=\"107\", \"Not=A?Brand\";v=\"24\"",
    #     "sec-ch-ua-mobile": "?0",
    #     "sec-ch-ua-platform": "\"Windows\""
    # }

    # for k, v in f5_dict.items():
    #     url = v.split('?')[0]
    #     params = {
    #         "token": v.split('=')[1]
    #     }
    #     print(f' ------ {k} BI链开始刷新 ------')
    #     response = requests.get(url, headers=headers, params=params)
    #     time.sleep(15)
    #     if response.status_code == 200:
    #         print(f' ------ {k} BI链刷新成功 ------')

    if error_logs:
        body = "".join(error_logs)
        send_email(f"京东商智报错信息_{getTimeStr()}", body)
    if error_logs2:
        body = "".join(error_logs2)
        h = str_html("“.*”", body)
        send_email(
            f"京东商智报错信息_{getTimeStr()}", h, ["shuju_python@bi-cheng.cn"], "html"
        )
