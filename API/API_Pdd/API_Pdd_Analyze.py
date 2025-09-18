import json
import os
import sys

from retrying import retry

from settings import table_mapping

"""
初始化几个映射文件
"""
path_ = os.path.join(os.path.dirname(__file__), "Pdd_Backend_Mapping.json")
path_2 = os.path.join(os.path.dirname(__file__), "CN_Table_Field.json")
path_3 = os.path.join(os.path.dirname(__file__), "CN_EN_Mapping.json")
with open(path_, 'r', encoding='utf8') as f:
    pdd_backend_mapping = json.load(f)
with open(path_2, 'r', encoding='utf8') as f2:
    cn_table_field = json.load(f2)
with open(path_3, 'r', encoding='utf8') as f3:
    cn_en_mapping = json.load(f3)


def en_to_cn(data: dict, cn_en_key: str, cn_table_field_key: str):
    """
    匹配pdd后台的中英文映射关系
    :param data:
    :param cn_en_key:
    :param cn_table_field_key:
    :return: 中文的item
    """
    d = {}
    p = []
    for i in cn_table_field[cn_table_field_key]:
        if "_" in i:
            j = i.split("_")
            d[j[0]] = j[1]
            p.append(j[0])
        else:
            p.append(i)
    cn_item = {}
    for k in data.keys():
        if k in pdd_backend_mapping[cn_en_key].keys() and pdd_backend_mapping[cn_en_key][k] in p:
            cn_item[pdd_backend_mapping[cn_en_key][k]] = float(f"{round(data[k], 4):.4f}") if isinstance(data[k],
                                                                                                         float) else \
                data[k]
    for a, b in d.items():
        cn_item[b] = cn_item.pop(a)
    return cn_item


def cn_en_to_cus(en_item, cn_en_mapping_key):
    cn_item = {}
    for k, v in cn_en_mapping[cn_en_mapping_key].items():
        cn_item[k] = en_item[v]
    return cn_item


def service_data__after_sales_data__analyze(res_json):
    """
    pdd_数据中心_服务数据_售后数据 解析
    :param res_json:
    :return: 中英文的item
    """
    method_name = sys._getframe(0).f_code.co_name.rsplit("__", 1)[0]
    cn_table_name = table_mapping[method_name]["cn_table_name"]
    en_table_name = table_mapping[method_name]["en_table_name"]
    result = res_json["result"]
    en_item = result
    if result:
        cn_item = en_to_cn(result, "aftersale", "pdd_数据中心_服务数据_售后数据")
        # cn_item["统计日期"] = result["statDate"]
        return {
            "table_name": cn_table_name,
            "item": cn_item
        }, {
            "table_name": en_table_name,
            "item": None
        }
    else:
        return None, None


@retry(stop_max_attempt_number=3, wait_fixed=2000)
def trade_data__data_overview__analyze(res_json, font_dict):
    """
    pdd_数据中心_交易数据_数据总览 解析
    :param res_json:
    :return: 中英文的item
    """
    method_name = sys._getframe(0).f_code.co_name.rsplit("__", 1)[0]
    cn_table_name = table_mapping[method_name]["cn_table_name"]
    en_table_name = table_mapping[method_name]["en_table_name"]
    result = res_json["result"]["dayList"][-1]
    print(f"result:{result}")
    if result:
        en_item = {}
        for k, v in result.items():
            if isinstance(v, str):
                vv = repr(v)
                for u_k in font_dict.keys():
                    if u_k in vv:
                        vv = vv.replace(u_k, f"|{font_dict[u_k]}|")
                vv = vv.replace("|", "")
                en_item[k] = vv[1:-1]
            else:
                en_item[k] = v
        cn_item = en_to_cn(en_item, "transaction", "pdd_数据中心_交易数据_数据总览")
        print(f"cn_item:{cn_item}")
        return {
            "table_name": cn_table_name,
            "item": cn_item
        }, {
            "table_name": en_table_name,
            "item": None
        }
    else:
        return None, None


def flow_data__flow_board__analyze(res_json):
    """
    pdd_数据中心_流量数据 解析
    :param res_json:
    :return: 中英文的item
    """
    method_name = sys._getframe(0).f_code.co_name.rsplit("__", 1)[0]
    cn_table_name = table_mapping[method_name]["cn_table_name"]
    en_table_name = table_mapping[method_name]["en_table_name"]
    result = res_json["result"]
    en_item = result
    if result:
        cn_item = en_to_cn(result, "flow", "pdd_数据中心_流量数据")
        return {
            "table_name": cn_table_name,
            "item": cn_item
        }, {
            "table_name": en_table_name,
            "item": None
        }
    else:
        return None, None


def goods_data__goods_detail__analyze(res_json, font_dict):
    """
    pdd_数据中心_商品数据_商品明细_商品明细效果 解析
    :param res_json:
    :return: 中英文的items
    """
    method_name = sys._getframe(0).f_code.co_name.rsplit("__", 1)[0]
    cn_table_name = table_mapping[method_name]["cn_table_name"]
    en_table_name = table_mapping[method_name]["en_table_name"]
    cn_items = []
    en_items = []
    goodsDetailList = res_json["result"]["goodsDetailList"]
    totalNum = res_json["result"]["totalNum"]
    if goodsDetailList:
        for i in goodsDetailList:
            en_item = {}
            for k, v in i.items():
                if isinstance(v, str):
                    vv = repr(v)
                    for u_k in font_dict.keys():
                        if u_k in vv:
                            vv = vv.replace(u_k, f"|{font_dict[u_k]}|")
                    vv = vv.replace("|", "")
                    en_item[k] = vv[1:-1]
                else:
                    en_item[k] = v
            cn_item = cn_en_to_cus(en_item, "pdd_数据中心_商品数据_商品明细_商品明细效果")
            cn_items.append(cn_item)
            en_items.append(en_item)
        return {
            "table_name": cn_table_name,
            "item": cn_items
        }, {
            "table_name": en_table_name,
            "item": None
        }, totalNum
    else:
        return None, None, 0


def goods_data__goods_general_situation__analyze(res_json, font_dict):
    """
    pdd_数据中心_商品数据_商品概况 解析
    :param res_json:
    :return: 中英文的item
    """
    method_name = sys._getframe(0).f_code.co_name.rsplit("__", 1)[0]
    cn_table_name = table_mapping[method_name]["cn_table_name"]
    en_table_name = table_mapping[method_name]["en_table_name"]
    result = res_json["result"]
    if result:
        en_item = {}
        for k, v in result.items():
            if isinstance(v, str):
                vv = repr(v)
                for u_k in font_dict.keys():
                    if u_k in vv:
                        vv = vv.replace(u_k, f"|{font_dict[u_k]}|")
                vv = vv.replace("|", "")
                en_item[k] = vv[1:-1]
            else:
                en_item[k] = v
        cn_item = en_to_cn(en_item, "goods", cn_table_name)
        return {
            "table_name": cn_table_name,
            "item": cn_item
        }, {
            "table_name": en_table_name,
            "item": None
        }
    else:
        return None, None


def goods_data__goods_general_situation_realtime__analyze(res_json):
    """
    pdd_数据中心_商品数据_商品概况 实时数据 解析
    :param res_json:
    :return: 中英文的item
    """
    method_name = sys._getframe(0).f_code.co_name.rsplit("__", 1)[0]
    cn_table_name = table_mapping[method_name]["cn_table_name"]
    en_table_name = table_mapping[method_name]["en_table_name"]
    result = res_json["result"]
    if result:
        todayData = result["todayData"]
        return {
            "table_name": cn_table_name,
            "item": None
        }, {
            "table_name": en_table_name,
            "item": todayData
        }
    else:
        return None, None
