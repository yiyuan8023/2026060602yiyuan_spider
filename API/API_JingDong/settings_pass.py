# -*- coding: utf-8 -*-
# @Time : 2024/9/18 14:31
# @Author : Shao0000
# @Email : Shao0000@aliyun.com
# @File : settings_pass.py
# @Project : JDSZ
import os

MYSQL_HOST = "223.5.242.173"
MYSQL_USER = "IT_jishubu"
MYSQL_PASSWORD = "lujun58586@...."
MYSQL_DBNAME = os.environ.get("MYSQL_DB") if os.environ.get("MYSQL_DB") else "bc"
MYSQL_PORT = 3306
CHARSET = 'utf8mb4'
LOGFILE = False if os.environ.get("LOGFILE", "1") == "0" else True

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
# 等级JDSZ所有的脚本
JDSZ_API_SCRIPT_MAP = {
    "jd1_1_01_jdsz": ("JdSzTradeAPI", "fetch_trade_summary"),
    "jd1_1_09_jdsz": ("JdSzProductAPI", "fetch_product_analysis__category_analysis"),
    "jd1_1_07_jdsz": ("JdSzServiceAPI", "fetch_service_analysis__after_sale_service"),
    "jd1_1_02_jdsz": ("JdSzProductAPI", "fetch_product_analysis__product_detail"),
    "jd1_1_06_jdsz": ("JdSzProductAPI", "fetch_product_analysis__product_detail"),
    "jd1_1_08_jdsz": ("JdSzReportAPI", "fetch_report_analysis__my_report__excel"),
    "jd1_1_04_jdsz": ("JdSzCustomAPI", "fetch_fans_summary__data_summary"),
    "jd1_1_05_jdsz": ("JdSzCustomAPI", "fetch_vip_summary__data_summary")
}

SCRIPT_SET = list(JDSZ_API_SCRIPT_MAP.keys())

START_DATE_DAYS = -3
END_DATE_DAYS = -1

WAIT_TIME_MIN = 1
WAIT_TIME_MAX = 2
