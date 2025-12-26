def get_long_values(items):
    """
    对每个字段分别提取最长的value值，然后组合成一个新的字典
    参数:
    items: list of dict - 字典列表
    返回:
    dict: 每个字段上最长value组成的新字典
    """
    if not items:
        return {}

    # 获取所有字典的键（假设所有字典结构相同）
    all_keys = items[0].keys() if items else []

    result = {}

    for key in all_keys:
        # 找出该key在所有字典中最长的value
        max_value = None
        max_length = -1

        for item in items:
            if key in item:
                value = item[key]
                # 转换为字符串并计算长度
                str_value = str(value) if value is not None else ""
                if len(str_value) > max_length:
                    max_length = len(str_value)
                    max_value = value

        # 将最长的value添加到结果字典中
        result[key] = max_value

    return result


if __name__ == '__main__':
    # 测试函数
    items_ = [
        {'收票对象': '张家口天猫优品电子商务有限公司(TS7)', '对账单号': 'S202206223704331832',
         '账单生成时间': '2022-06-22'},
        {'收票对象': '张家口天猫优品电子商务有限公司', '对账单号': 'S20220622370433',
         '账单生成时间': '2022-06-22 14:00:07'}
    ]

    result_ = get_long_values(items_)
    print("提取结果:")
    print(result_)
