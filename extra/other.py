
def analyzing_res(res_json):
    # JSON数据，将嵌套的数据结构转换为扁平化的字典列表。
    # 将 {"字段名": {"value": "实际值"}} 转换为 {"字段名": "实际值"}
    if res_json:
        data = res_json["data"]
        items = []
        for i in data:
            item = {}
            for k, v in i.items():
                item[k] = v["value"]
            items.append(item)
        return items  # 修复：添加返回语句
    else:
        return None
