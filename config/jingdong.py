import os

from config.database import get_database_config

JDSZ_API_SCRIPT_MAP = {
    "jd1_1_01_jdsz": ("JdSzTradeAPI", "fetch_trade_summary"),
    "jd1_1_09_jdsz": ("JdSzProductAPI", "fetch_product_analysis__category_analysis"),
    "jd1_1_07_jdsz": ("JdSzServiceAPI", "fetch_service_analysis__after_sale_service"),
    "jd1_1_02_jdsz": ("JdSzProductAPI", "fetch_product_analysis__product_detail"),
    "jd1_1_06_jdsz": ("JdSzProductAPI", "fetch_product_analysis__product_detail"),
    "jd1_1_08_jdsz": ("JdSzReportAPI", "fetch_report_analysis__my_report__excel"),
    "jd1_1_04_jdsz": ("JdSzCustomAPI", "fetch_fans_summary__data_summary"),
    "jd1_1_05_jdsz": ("JdSzCustomAPI", "fetch_vip_summary__data_summary"),
}

SCRIPT_SET = list(JDSZ_API_SCRIPT_MAP.keys())

START_DATE_DAYS = int(os.environ.get("JDSZ_START_DATE_DAYS", -3))
END_DATE_DAYS = int(os.environ.get("JDSZ_END_DATE_DAYS", -1))
WAIT_TIME_MIN = int(os.environ.get("JDSZ_WAIT_TIME_MIN", 1))
WAIT_TIME_MAX = int(os.environ.get("JDSZ_WAIT_TIME_MAX", 2))


def get_jingdong_database_config():
    return get_database_config("jingdong")
