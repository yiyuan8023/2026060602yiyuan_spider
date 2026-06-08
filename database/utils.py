CONTROL_CHAR_TRANS = str.maketrans("", "", "".join(chr(i) for i in range(32)) + chr(127) + "'")


def clean_db_value(value):
    """清理数据库不适合保存的控制字符和单引号。"""
    if isinstance(value, str):
        return value.translate(CONTROL_CHAR_TRANS)
    return value


def get_ordered_keys(items):
    """按记录出现顺序收集字段，保证建表和写入列顺序稳定。"""
    keys = []
    seen = set()
    for item in items:
        for key in item.keys():
            if key not in seen:
                keys.append(key)
                seen.add(key)
    return keys


def get_longest_values(items, max_rows=1000):
    """取每个字段样本中最长的值，用于更稳妥地推断列宽。"""
    sample_items = items[:max_rows]
    result = {}
    for key in get_ordered_keys(sample_items):
        max_value = None
        max_length = -1
        for item in sample_items:
            if key not in item:
                continue
            value = item[key]
            value_length = len(str(value)) if value is not None else 0
            if value_length > max_length:
                max_value = value
                max_length = value_length
        result[key] = max_value
    return result


def quote_identifier(identifier):
    """安全引用表名或字段名，避免反引号破坏 SQL 结构。"""
    identifier = str(identifier)
    if not identifier:
        raise ValueError("数据库标识符不能为空")
    if "\x00" in identifier:
        raise ValueError(f"数据库标识符包含非法字符: {identifier!r}")
    return f"`{identifier.replace('`', '``')}`"
