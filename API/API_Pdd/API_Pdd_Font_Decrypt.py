def pdd_font_decrypt_api(res_data, font_dict):
    """
    数据替换，加密字符替换为真实数字
    :param res_data:
    :return: 中英文的items"""

    for i in res_data:
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


def decrypt_unicode_string(encrypted_str, font_dict):
    """
    解密包含unicode转义序列的字符串

    :param encrypted_str: 加密字符串
    :param font_dict: 解密字典
    :return: 解密后的数字字符串
    """
    # 构建实际字符到数字的映射
    char_to_digit = {}
    for unicode_escape, digit in font_dict.items():
        try:
            # 将 "\\ueade" 格式的字符串转换为实际的unicode字符
            actual_char = unicode_escape.encode().decode("unicode_escape")
            char_to_digit[actual_char] = digit
        except UnicodeDecodeError:
            continue

    # print(char_to_digit)
    # 解密字符串
    result = ""
    if isinstance(encrypted_str, str):
        for char in encrypted_str:
            if char in char_to_digit:
                result += char_to_digit[char]
            else:
                # 如果找不到对应字符，返回原值
                result += char  # 这里选择跳过未知字符
        return result
    else:
        return encrypted_str


def res_decrypt(res_data_list, font_dict, dict_str):
    # 数据包解密,并做中文字段映射
    items = []
    for res_data in res_data_list:
        decrypt_item = {}
        item = {}
        for k, v in res_data.items():
            decrypt_item[k] = decrypt_unicode_string(v, font_dict)  # 解密

        # 根据dict_str映射将英文字段转换为中文字段
        for en_key, cn_key in dict_str.items():
            if en_key in decrypt_item:
                item[cn_key] = decrypt_item[en_key]
        items.append(item)
    return items


if __name__ == "__main__":
    encrypted_string = "\uefb4\ue5c0\ue4d6.3"
    # encrypted_string = '我是商品'
    decrypt_dictionary = {
        "\\ue6ad": "5",
        "\\ueb37": "8",
        "\\ue581": "3",
        "\\ue5c0": "1",
        "\\ueba3": "0",
        "\\uec4a": "2",
        "\\ue72e": "6",
        "\\uefb5": "7",
        "\\ue4d6": "9",
        "\\ue858": "4",
    }

    decrypted_result = decrypt_unicode_string(encrypted_string, decrypt_dictionary)
    print(f"解密结果: {decrypted_result}")
