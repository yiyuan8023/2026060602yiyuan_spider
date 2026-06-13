# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-10 21:35:53
- 最近修改：2026-06-12 14:33:20
- 文件用途：解析商家工作台订单详情消费者视角优惠明细，将平台 JSON 转为数据库可写入字段。
- 业务范围：适用于 API_TaoXi_GongZuoTai 订单详情接口返回的 soldDetailPriceModule 价格组成结构。
- 依赖入口：使用标准库 json 和 re，对外暴露 parse_order_discount_details。
- 验收方式：修改后执行 py_compile；使用订单详情样本验证优惠项、购物券/红包/消费券归一、币种剥离和备注保留。
- 注意事项：解析器不请求平台、不写数据库、不记录敏感响应；原始 json_data 由 API 层显式返回给任务脚本写入独立分表。
"""

import re


CURRENCY_CODE_PATTERN = re.compile(r"(?<![A-Z])([A-Z]{3})(?![A-Z])")


def _normalize_label(label):
    """把平台细分优惠字段归一到稳定入库字段。"""
    if "红包" in label:
        return "红包", "红包备注"
    if "天猫购物券" in label:
        return "购物券", "购物券备注"
    if "消费券" in label:
        return "消费券", "消费券备注"
    return label, None


def _clean_money(value):
    value_text = str(value)
    currency_codes = CURRENCY_CODE_PATTERN.findall(value_text)
    cleaned_value = value_text.replace("￥", "")
    for currency_code in currency_codes:
        cleaned_value = cleaned_value.replace(currency_code, "")
    return cleaned_value.strip(), currency_codes


def _append_value(result_dict, field_name, value, note_field=None, note_value=None):
    if field_name in result_dict and result_dict[field_name]:
        result_dict[field_name] = f"{result_dict[field_name]}/{value}"
    else:
        result_dict[field_name] = value

    if note_field and note_value:
        if note_field in result_dict and result_dict[note_field]:
            result_dict[note_field] = f"{result_dict[note_field]}/{note_value}"
        else:
            result_dict[note_field] = note_value


def _extract_consumer_detail(price_compositions):
    """从订单价格模块中定位消费者视角优惠明细。"""
    for price_item in price_compositions:
        onclick = price_item.get("onClick") or {}
        main_params = (onclick.get("main") or {}).get("params") or {}
        if main_params.get("title") != "消费者视角优惠明细":
            continue
        for schema_item in main_params.get("schemaContent") or []:
            if schema_item.get("type") == "PriceComposition":
                return (schema_item.get("params") or {}).get("compose") or []
    return []


def _parse_consumer_detail(consumer_detail):
    """解析消费者视角优惠明细，并保留特殊消费券子项。"""
    result_dict = {}
    currency_codes = []

    for detail_item in consumer_detail:
        if "value" not in detail_item:
            continue

        label = detail_item["label"]
        field_name, note_field = _normalize_label(label)
        value, item_currency_codes = _clean_money(detail_item["value"])
        _append_value(result_dict, field_name, value, note_field, label)
        currency_codes.extend(item_currency_codes)

        for sub_item in detail_item.get("subItems") or []:
            if "value" not in sub_item:
                continue
            if "label" not in sub_item:
                continue
            sub_label = sub_item["label"]
            sub_field_name, sub_note_field = _normalize_label(sub_label)
            sub_value, sub_currency_codes = _clean_money(sub_item["value"])
            _append_value(
                result_dict,
                sub_field_name,
                sub_value,
                sub_note_field,
                sub_label,
            )
            currency_codes.extend(sub_currency_codes)

    return result_dict, sorted(set(currency_codes))


def parse_order_discount_details(response_data):
    """解析订单详情响应，返回优惠明细业务字段。"""
    result_dict, currency_codes = _parse_consumer_detail(
        _extract_consumer_detail(response_data.get("soldDetailPriceModule") or [])
    )

    if currency_codes:
        result_dict["备注"] = "/".join(currency_codes)
    return result_dict
