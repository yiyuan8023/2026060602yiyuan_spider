# -*- coding: utf-8 -*-
"""
Development notes:
- Author: Yiyuan
- Created: 2026-06-26 12:20:00
- Purpose: Normalize WeCom Docs New Retail customer-follow smartsheet records.
- Scope: Sheet "客户跟进" in document "新零售台账".
- Validation: py_compile, local xlsx header probe, and read-only online decode probe.
- Safety: Parser does not request network or write database.
"""

from datetime import datetime, timedelta
import re

from date_utils import get_date, get_is_date


EXPECTED_HEADERS = [
    "客户名称",
    "登记时间",
    "联系电话",
    "客户微信（可添加外部联系人）",
    "成交意向",
    "线索来源",
    "订单总价",
    "分配门店",
    "销售对接人",
    "对接群（可添加外部群）",
    "成交日期",
    "KA单号",
    "最新进度",
    "跟进节点1-回访日期（一天后）",
    "客户跟进记录",
    "跟进节点2-交付日期",
    "客户跟进记录2",
    "跟进节点3",
    "跟进节点4",
    "跟进节点5-合同到期",
    "收款日期",
    "单选",
    "地址",
    "跟进记录3",
    "跟进记录4",
    "根据记录",
    "跟进记录",
    "单选 2",
    "分配门店 2",
]

DATE_FIELDS = {
    "登记时间",
    "成交日期",
    "跟进节点1-回访日期（一天后）",
    "跟进节点2-交付日期",
    "跟进节点3",
    "跟进节点4",
    "跟进节点5-合同到期",
    "收款日期",
}


def parse_new_retail_customer_follow_records(
    raw_records,
    *,
    source_site,
    source_url,
    file_info=None,
    sheet_name="客户跟进",
):
    """Normalize decoded WeCom Docs rows and append source-tracking fields."""
    file_info = file_info or {}
    items = []
    for raw_item in raw_records:
        if _is_empty_row(raw_item):
            continue

        item = {field: _normalize_cell(raw_item.get(field, "")) for field in EXPECTED_HEADERS}
        for field in DATE_FIELDS:
            item[field] = _normalize_date(item.get(field))

        item["来源站点"] = source_site
        item["来源URL"] = source_url
        item["来源文件ID"] = str(file_info.get("local_pad_id") or file_info.get("id") or "")
        item["来源文件名"] = str(file_info.get("title") or "")
        item["来源Sheet"] = sheet_name
        items.append(item)
    return items


def validate_new_retail_customer_follow_headers(raw_records):
    """Check whether the selected sheet exposes the expected business columns."""
    if not raw_records:
        raise ValueError("企微文档新零售台账客户跟进没有读取到数据")

    actual_headers = set(raw_records[0].keys())
    missing_headers = [field for field in EXPECTED_HEADERS if field not in actual_headers]
    if missing_headers:
        raise ValueError(f"企微文档新零售台账客户跟进缺少字段: {missing_headers}")


def _is_empty_row(raw_item):
    return not any(_normalize_cell(value) for key, value in raw_item.items() if not str(key).startswith("__"))


def _normalize_cell(value):
    if value is None:
        return ""
    return str(value).strip()


def _normalize_date(value):
    if not value:
        return ""
    value = _normalize_cell(value)
    if get_is_date(value):
        return get_date(value, "%Y-%m-%d")
    if _looks_like_excel_serial(value):
        dt = datetime(1899, 12, 30) + timedelta(days=float(value))
        return dt.strftime("%Y-%m-%d")

    match = re.fullmatch(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日?", value)
    if match:
        year, month, day = (int(part) for part in match.groups())
        return f"{year:04d}-{month:02d}-{day:02d}"

    match = re.fullmatch(r"(\d{1,2})[./月](\d{1,2})日?", value)
    if match:
        month, day = (int(part) for part in match.groups())
        return f"{datetime.now().year:04d}-{month:02d}-{day:02d}"

    return value


def _looks_like_excel_serial(value):
    try:
        serial = float(value)
    except ValueError:
        return False
    return 20000 <= serial <= 80000
