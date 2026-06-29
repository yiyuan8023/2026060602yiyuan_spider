# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-26 09:52:00
- 最近修改：2026-06-26 09:52:00
- 文件用途：解析腾讯文档《安徽KA壁挂炉发货对接》中的发货明细 Sheet，校验表头并归一化日期字段。
- 业务范围：适用于腾讯文档安徽KA壁挂炉发货明细入库字段，目标数据由任务脚本补充来源站点和文档信息。
- 依赖入口：使用 date_utils.get_date、date_utils.get_is_date。
- 验收方式：执行 py_compile；通过本地上传样本和在线导出验证 19 列表头、订单日期、发货时间和有效行过滤结果。
- 注意事项：parser 不发起网络请求、不写数据库、不输出手机号、地址、SN码等明细内容。
"""

from datetime import datetime, timedelta

from date_utils import get_date, get_is_date


EXPECTED_HEADERS = [
    "年月",
    "序号",
    "订单日期",
    "店铺",
    "平台单号",
    "特殊备注",
    "商品代码",
    "数量",
    "结算单价",
    "结算总价",
    "姓名",
    "电话",
    "地址",
    "发货单号",
    "发货时间",
    "SN码",
    "备注",
    "赠品",
    "发票",
]

DATE_FIELDS = {"订单日期", "发货时间"}
REQUIRED_DATE_FIELD = "订单日期"


def parse_anhui_ka_delivery_records(
    raw_records,
    *,
    source_site,
    source_url,
    file_info=None,
    sheet_name="发货明细",
):
    """Normalize Tencent Docs Excel rows and append source-tracking fields."""
    file_info = file_info or {}
    items = []
    for raw_item in raw_records:
        if _is_empty_row(raw_item):
            continue

        item = {field: _normalize_cell(raw_item.get(field, "")) for field in EXPECTED_HEADERS}
        for field in DATE_FIELDS:
            item[field] = _normalize_date(item.get(field))
        if not item[REQUIRED_DATE_FIELD]:
            continue

        item["来源站点"] = source_site
        item["来源URL"] = source_url
        item["来源文件ID"] = str(file_info.get("local_pad_id") or "")
        item["来源文件名"] = str(file_info.get("title") or "")
        item["来源Sheet"] = sheet_name
        items.append(item)
    return items


def validate_anhui_ka_delivery_headers(raw_records):
    """Check whether the downloaded sheet exposes the expected business columns."""
    if not raw_records:
        raise ValueError("腾讯文档安徽KA发货明细没有读取到数据")

    actual_headers = set(raw_records[0].keys())
    missing_headers = [field for field in EXPECTED_HEADERS if field not in actual_headers]
    if missing_headers:
        raise ValueError(f"腾讯文档安徽KA发货明细缺少字段: {missing_headers}")


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
    if _looks_like_excel_serial(value):
        dt = datetime(1899, 12, 30) + timedelta(days=float(value))
        return dt.strftime("%Y-%m-%d")
    return value


def _looks_like_excel_serial(value):
    try:
        serial = float(value)
    except ValueError:
        return False
    return 20000 <= serial <= 80000
