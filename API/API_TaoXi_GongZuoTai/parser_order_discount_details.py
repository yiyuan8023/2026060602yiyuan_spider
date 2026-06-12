# -*- coding: utf-8 -*-
"""
开发说明：
- 作者：一元
- 创建时间：2026-06-10 21:35:53
- 最近修改：2026-06-10 21:36:12
- 文件用途：解析商家工作台订单详情消费者视角优惠明细，将平台 JSON 转为数据库可写入字段。
- 业务范围：适用于 API_TaoXi_GongZuoTai 订单详情接口返回的 soldDetailPriceModule 价格组成结构。
- 依赖入口：使用标准库 json，对外暴露 parse_order_discount_details。
- 验收方式：修改后执行 py_compile；使用订单详情样本验证优惠项、特殊消费券子项、币种备注和 raw_json_data 保留。
- 注意事项：解析器不请求平台、不写数据库、不记录敏感响应；保留 raw_json_data 供平台字段变更时追溯。
"""

import json


def _clean_money(value):
    return str(value).replace("￥", "").replace("HKD", "").replace("MOP", "")


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
    for detail_item in consumer_detail:
        if "value" not in detail_item:
            continue

        label = detail_item["label"]
        result_dict[label] = _clean_money(detail_item["value"])
        if label == "红包(使用满3000减300消费券)":
            for sub_item in detail_item.get("subItems") or []:
                result_dict[sub_item["label"]] = _clean_money(sub_item["value"])
    return result_dict


def parse_order_discount_details(response_data):
    """解析订单详情响应，返回优惠明细字段和原始响应留痕。"""
    json_data = json.dumps(response_data, ensure_ascii=False)
    result_dict = _parse_consumer_detail(
        _extract_consumer_detail(response_data.get("soldDetailPriceModule") or [])
    )

    # 兼容历史表字段 json_data，同时新增 raw_json_data 作为平台原始响应留痕。
    result_dict["json_data"] = json_data
    result_dict["raw_json_data"] = json_data
    if "HKD" in json_data:
        result_dict["备注"] = "HKD"
    elif "MOP" in json_data:
        result_dict["备注"] = "MOP"
    return result_dict
