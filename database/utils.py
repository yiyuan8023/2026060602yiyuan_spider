CONTROL_CHAR_TRANS = str.maketrans("", "", "".join(chr(i) for i in range(32)) + chr(127) + "'")


def clean_db_value(value):
    if isinstance(value, str):
        return value.translate(CONTROL_CHAR_TRANS)
    return value


def get_ordered_keys(items):
    keys = []
    seen = set()
    for item in items:
        for key in item.keys():
            if key not in seen:
                keys.append(key)
                seen.add(key)
    return keys


def get_longest_values(items, max_rows=1000):
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
    identifier = str(identifier)
    if not identifier:
        raise ValueError("数据库标识符不能为空")
    if "\x00" in identifier:
        raise ValueError(f"数据库标识符包含非法字符: {identifier!r}")
    return f"`{identifier.replace('`', '``')}`"
