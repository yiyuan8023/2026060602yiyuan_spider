def en_to_cn(date_list, dict_str):
    # 将英文字段转换成中文字段,只保留想要的字段
    items = []
    for date in date_list:
        item = {}
        for k, v in dict_str.items():
            item[v] = date.get(k, "")

        items.append(item)

    return items


if __name__ == "__main__":
    _dict_str = {
        "OrdAmt": "成交金额",
        "PV": "浏览量",
        "ShelvesNumSPU": "上架商品数(SPU)",
        "DealCustNum": "成交客户数",
        "AddBuyGoodsNum": "加购商品件数",
        "UV": "访客数",
        "SecondName": "二级类目",
        "DealCustRate": "成交转化率",
        "ThirdName": "三级类目",
    }

    _date_list = [
        {
            "OrdAmt": "89560.58999999995",
            "PV": 8125,
            "OrdAmt_HB": "-0.14491250639330241",
            "INDSECCATID": "12402",
            "GuideClickCustRate_HB": None,
            "UV_HB": "0.2953784326858674",
            "SHOP": "743102",
            "ShelvesNumSPU": 42,
            "INDTHICATID": "12405",
            "DealCustRate_HB": "0.9910845014180841",
            "ShelvesNumSPU_HB": 0,
            "PV_HB": "0.5443831971108154",
            "DealCustNum": 521,
            "ShelvesNumSKU_HB": 0,
            "AddBuyGoodsNum": 742,
            "UV": 1934,
            "GuideClickCustRate": 0,
            "SecondName": "汽车服务",
            "AddBuyGoodsNum_HB": "1.2083333333333333",
            "DealCustNum_HB": "1.5792079207920793",
            "DealCustRate": "0.2693898655635988",
            "ShelvesNumSKU": 730,
            "GuideDealCustRate_HB": None,
            "ThirdName": "保养服务",
            "CategoryName": "保养服务",
            "GuideDealCustRate": 0,
        },
    ]

    _items = en_to_cn(_date_list, _dict_str)
    print(_items)
