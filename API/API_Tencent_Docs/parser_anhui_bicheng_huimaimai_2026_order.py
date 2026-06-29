# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-26 11:10:00
- 最近修改：2026-06-26 11:10:00
- 文件用途：解析腾讯文档《安徽碧橙&慧买卖在线报表单-林内》中的“2026订单”Sheet，校验表头并归一化日期字段。
- 业务范围：适用于腾讯文档安徽碧橙慧买卖 2026 订单数据入库字段，目标数据由任务脚本补充来源站点和文档信息。
- 依赖入口：使用 date_utils.get_date、date_utils.get_is_date。
- 验收方式：执行 py_compile；通过在线导出样本验证 18 个有效表头、日期字段归一化和来源字段补充。
- 注意事项：parser 不发起网络请求、不写数据库、不输出电话、地址、SN码等明细内容；不默认过滤日期为空行。
"""

from datetime import datetime, timedelta

from date_utils import get_date, get_is_date


EXPECTED_HEADERS = [
    "订单日期",
    "店铺",
    "序号",
    "平台单号",
    "订单编号",
    "商品代码",
    "销售数量",
    "销售单价",
    "销售金额（GMV）",
    "姓名",
    "电话",
    "地址",
    "是否赠送赠品（数量默认1）",
    "发货单号",
    "发货时间",
    "SN码",
    "备注",
    "结算进度-对账人员填写",
]

DATE_FIELDS = {"订单日期", "发货时间"}


def parse_anhui_bicheng_huimaimai_2026_order_records(
    raw_records,
    *,
    source_site,
    source_url,
    file_info=None,
    sheet_name="2026订单",
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

        item["来源站点"] = source_site
        item["来源URL"] = source_url
        item["来源文件ID"] = str(file_info.get("local_pad_id") or "")
        item["来源文件名"] = str(file_info.get("title") or "")
        item["来源Sheet"] = sheet_name
        items.append(item)
    return items


def validate_anhui_bicheng_huimaimai_2026_order_headers(raw_records):
    """Check whether the downloaded sheet exposes the expected business columns."""
    if not raw_records:
        raise ValueError("腾讯文档安徽碧橙慧买卖2026订单没有读取到数据")

    actual_headers = set(raw_records[0].keys())
    missing_headers = [field for field in EXPECTED_HEADERS if field not in actual_headers]
    if missing_headers:
        raise ValueError(f"腾讯文档安徽碧橙慧买卖2026订单缺少字段: {missing_headers}")


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
