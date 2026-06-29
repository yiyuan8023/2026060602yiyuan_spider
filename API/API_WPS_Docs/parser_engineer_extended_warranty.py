# -*- coding: utf-8 -*-
"""Parse WPS document rows for engineer extended warranty sales."""

from date_utils import get_date, get_is_date


EXPECTED_HEADERS = [
    "时间",
    "用户名称",
    "电话",
    "服务单号",
    "机器型号",
    "地址",
    "机器品类",
    "延保费用",
    "延保时间",
    "工程师",
    "延保卡号",
    "已结算",
    "备注",
]


def parse_engineer_extended_warranty_records(
    raw_records,
    *,
    source_site,
    source_url,
    file_info=None,
    sheet_name="9月延保登记",
):
    """Normalize KDocs Excel rows and append source-tracking fields."""
    file_info = file_info or {}
    items = []
    for raw_item in raw_records:
        if _is_empty_row(raw_item):
            continue

        item = {field: _normalize_cell(raw_item.get(field, "")) for field in EXPECTED_HEADERS}
        item["时间"] = _normalize_date(item.get("时间"))
        if not item["时间"]:
            continue

        item["来源站点"] = source_site
        item["来源URL"] = source_url
        item["来源文件ID"] = str(file_info.get("id") or "")
        item["来源文件名"] = str(file_info.get("name") or "")
        item["来源Sheet"] = sheet_name
        items.append(item)
    return items


def validate_engineer_extended_warranty_headers(raw_records):
    """Check whether the downloaded sheet exposes the expected business columns."""
    if not raw_records:
        raise ValueError("工程师延保销售表没有读取到数据")

    actual_headers = set(raw_records[0].keys())
    missing_headers = [field for field in EXPECTED_HEADERS if field not in actual_headers]
    if missing_headers:
        raise ValueError(f"工程师延保销售表缺少字段: {missing_headers}")


def _is_empty_row(raw_item):
    return not any(_normalize_cell(value) for value in raw_item.values())


def _normalize_cell(value):
    if value is None:
        return ""
    return str(value).strip()


def _normalize_date(value):
    if not value:
        return ""
    if get_is_date(value):
        return get_date(value, "%Y-%m-%d")
    return value
