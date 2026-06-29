# -*- coding: utf-8 -*-
"""Parse WPS document rows for 阙里代发 order fulfillment."""

from date_utils import get_date, get_is_date


EXPECTED_HEADERS = [
    "店铺",
    "订单日期",
    "序号",
    "销售平台",
    "平台单号",
    "订单编号-发货平台单号",
    "商品代码",
    "数量",
    "订单金额",
    "客户姓名",
    "手机号",
    "收货地址",
    "发货单号",
    "SN码",
    "备注",
    "代发运费",
]


def parse_queli_daifa_records(
    raw_records,
    *,
    source_site,
    source_url,
    file_info=None,
    sheet_name="阙里代发",
):
    """Normalize KDocs Excel rows and append source-tracking fields."""
    file_info = file_info or {}
    items = []
    for raw_item in raw_records:
        if _is_empty_row(raw_item):
            continue

        item = {field: _normalize_cell(raw_item.get(field, "")) for field in EXPECTED_HEADERS}
        item["订单日期"] = _normalize_date(item.get("订单日期"))
        if not item["订单日期"]:
            continue

        item["来源站点"] = source_site
        item["来源URL"] = source_url
        item["来源文件ID"] = str(file_info.get("id") or "")
        item["来源文件名"] = str(file_info.get("name") or "")
        item["来源Sheet"] = sheet_name
        items.append(item)
    return items


def validate_queli_daifa_headers(raw_records):
    """Check whether the downloaded sheet exposes the expected business columns."""
    if not raw_records:
        raise ValueError("阙里代发文档没有读取到数据")

    actual_headers = set(raw_records[0].keys())
    missing_headers = [field for field in EXPECTED_HEADERS if field not in actual_headers]
    if missing_headers:
        raise ValueError(f"阙里代发文档缺少字段: {missing_headers}")


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
