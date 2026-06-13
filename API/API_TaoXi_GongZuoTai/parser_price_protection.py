# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-12 18:21:46
- 最近修改：2026-06-12 18:21:46
- 文件用途：解析千牛价保管理价保记录 JSON，将平台字段转为数据库可写入中文字段并保留 raw_json_data。
- 业务范围：适用于 /priceprotection/record_list.do 返回的价保订单赔付记录。
- 依赖入口：使用标准库 json、datetime 和 urllib.parse，对外暴露 build_price_protection_records。
- 验收方式：修改后执行 py_compile；使用接口单页样本验证订单号、金额、商品信息、时间字段和 raw_json_data。
- 注意事项：解析器不请求平台、不写数据库、不记录敏感响应；嵌套原始字段统一放入 raw_json_data 便于后续排查平台变更。
"""

import json
import re
from datetime import datetime
from html import unescape
from io import BytesIO
from urllib.parse import unquote

from excel_tool.reader import read_excel_dataframe


EXPORT_HEADER_MAPPING = {
    ("主订单ID", ""): "主订单ID",
    ("子订单ID", ""): "子订单ID",
    ("购买商品信息", "商品标题"): "购买商品标题",
    ("购买商品信息", "商品ID"): "购买商品ID",
    ("购买商品信息", "SKUID"): "购买商品SKU ID",
    ("购买商品信息", "具体型号"): "购买商品规格",
    ("价差金额", ""): "价差金额",
    ("逆向退款金额（含退还天猫积分类服务费）", ""): "逆向退款金额",
    ("申请时间", ""): "申请时间",
    ("状态", ""): "状态",
    ("备注", ""): "备注",
}


def _format_timestamp(timestamp):
    if timestamp in (None, ""):
        return None
    try:
        return datetime.fromtimestamp(int(timestamp) / 1000).strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError, OSError):
        return None


def _item_value(item_data, key):
    if not isinstance(item_data, dict):
        return None
    value = item_data.get(key)
    return value if value not in ("", None) else None


def _decode_url(value):
    if not value:
        return None
    return unquote(str(value))


def _normalize_text(value):
    if value in (None, ""):
        return None
    text = str(value).strip()
    return text or None


def _normalize_money(value):
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = re.sub(r"[^\d.\-]", "", str(value))
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _normalize_datetime_text(value):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value).strip() or None


def _decode_html_text(value):
    text = _normalize_text(value)
    return unescape(text) if text else None


def _normalize_header_value(value):
    text = _normalize_text(value)
    if not text:
        return ""
    if text.startswith("Unnamed:"):
        return ""
    return text


def _flatten_export_headers(columns):
    flat_headers = []
    for column in columns:
        if isinstance(column, tuple):
            first_level = _normalize_header_value(column[0])
            second_level = _normalize_header_value(column[1] if len(column) > 1 else None)
        else:
            first_level = _normalize_header_value(column)
            second_level = ""

        flat_headers.append(
            EXPORT_HEADER_MAPPING.get((first_level, second_level))
            or EXPORT_HEADER_MAPPING.get((first_level, ""))
            or second_level
            or first_level
        )
    return flat_headers


def build_price_protection_record(raw_record, shop_name=None):
    """把单条价保记录转为中文业务字段。"""
    original_item = raw_record.get("originalItem") or {}
    compare_item = raw_record.get("compareItem") or {}
    refund_detail = raw_record.get("refundDetail") or {}
    refund_fee_spec = refund_detail.get("refundFeeSpecDTO") or {}

    return {
        "店铺名称": shop_name,
        "价保申请ID": raw_record.get("applyId"),
        "主订单ID": raw_record.get("mainOrderId"),
        "子订单ID": raw_record.get("orderId"),
        "用户昵称": raw_record.get("userNick"),
        "申请时间": _format_timestamp(raw_record.get("applyTime")),
        "价保状态": raw_record.get("statusDescription"),
        "价保状态码": raw_record.get("tabType"),
        "审核提示": raw_record.get("auditMsg") or raw_record.get("msg"),
        "价保服务开始时间": _format_timestamp(raw_record.get("ppStartTime")),
        "价保服务结束时间": _format_timestamp(raw_record.get("ppEndTime")),
        "商家审核截止时间": _format_timestamp(raw_record.get("sellerAuditEndTime")),
        "购买商品ID": _item_value(original_item, "itemId"),
        "购买商品SKU ID": _item_value(original_item, "skuId"),
        "购买商品标题": _item_value(original_item, "itemTitle"),
        "购买商品规格": _item_value(original_item, "specialType"),
        "购买商品链接": _decode_url(_item_value(original_item, "itemUrl")),
        "同款商品ID": _item_value(compare_item, "itemId"),
        "同款商品SKU ID": _item_value(compare_item, "skuId"),
        "同款商品标题": _item_value(compare_item, "itemTitle"),
        "同款商品规格": _item_value(compare_item, "specialType"),
        "同款商品链接": _decode_url(_item_value(compare_item, "itemUrl")),
        "本次价保金额": raw_record.get("refundFee") or refund_detail.get("refundFee"),
        "原始金额": refund_detail.get("originalFee"),
        "支付金额": refund_detail.get("payMoney"),
        "优惠金额": refund_detail.get("discountFee"),
        "商品优惠金额": refund_detail.get("itemPromotionFee"),
        "平台支付金额": refund_detail.get("platformRefundFee"),
        "平台垫付金额": refund_fee_spec.get("platformAdvancedFeeString"),
        "平台实付金额": refund_fee_spec.get("actualPlatformFeeString"),
        "商家支付金额": refund_detail.get("sellerRefundFee"),
        "历史已退金额": refund_detail.get("historyRefundedFee"),
        "价保订单ID": refund_detail.get("priceInsuranceOrderId"),
        "申请结果ID": refund_detail.get("applyResultId"),
        "是否显示明细按钮": raw_record.get("showDetailBtn"),
        "raw_json_data": json.dumps(raw_record, ensure_ascii=False, default=str),
    }


def build_price_protection_records(raw_records, shop_name=None):
    """批量解析价保记录。"""
    return [
        build_price_protection_record(raw_record, shop_name=shop_name)
        for raw_record in raw_records or []
        if isinstance(raw_record, dict)
    ]


def build_price_protection_export_records(
    excel_content,
    shop_name=None,
    query_start_time=None,
    query_end_time=None,
):
    """解析价保订单赔付详情导出 Excel，按导出字段生成可入库记录。"""
    if isinstance(excel_content, bytes):
        excel_content = BytesIO(excel_content)

    df = read_excel_dataframe(
        excel_content,
        sheet_name=0,
        header=[0, 1],
        dtype=str,
        engine="openpyxl",
    )
    df.columns = _flatten_export_headers(df.columns)
    df = df.loc[:, [column for column in df.columns if column]]
    df = df.dropna(how="all")

    records = []
    for row in df.fillna("").to_dict("records"):
        item = {
            "店铺名称": shop_name,
            "主订单ID": _normalize_text(row.get("主订单ID")),
            "子订单ID": _normalize_text(row.get("子订单ID")),
            "购买商品标题": _decode_html_text(row.get("购买商品标题")),
            "购买商品ID": _normalize_text(row.get("购买商品ID")),
            "购买商品SKU ID": _normalize_text(row.get("购买商品SKU ID")),
            "购买商品规格": _decode_html_text(row.get("购买商品规格")),
            "价差金额": _normalize_money(row.get("价差金额")),
            "逆向退款金额": _normalize_money(row.get("逆向退款金额")),
            "申请时间": _normalize_datetime_text(row.get("申请时间")),
            "状态": _normalize_text(row.get("状态")),
            "备注": _decode_html_text(row.get("备注")),
            "查询开始时间": query_start_time,
            "查询结束时间": query_end_time,
            "raw_excel_row_data": json.dumps(row, ensure_ascii=False, default=str),
        }
        if not item["主订单ID"] and not item["子订单ID"]:
            continue
        records.append(item)
    return records
