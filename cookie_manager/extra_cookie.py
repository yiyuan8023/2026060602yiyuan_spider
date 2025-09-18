from typing import List, Dict, Optional

from fake_useragent import UserAgent


def get_ramdom_ua():
    # 获取一个随机UA
    return str(UserAgent().random)


def cookiejar_to_cookie_str(cookie_jar) -> str:
    """
    将 http.cookiejar.CookieJar 对象转换为标准的 Cookie 字符串。
    :param cookie_jar: CookieJar 对象
    :return: Cookie 字符串，如 'key1=value1; key2=value2'
    """
    cookies = {}
    for cookie_value in cookie_jar:
        cookies[cookie_value["name"]] = cookie_value["value"]
    return "; ".join([f"{name}={value}" for name, value in cookies.items()])


def cookie_str_to_dict(cookie_str):
    """
    将 Cookie 字符串转换为字典。
    参数:- cookie_str (str): Cookie 字符串，例如 "key1=value1; key2=value2; key3=value3"
    返回:- dict: 包含键值对的字典。
    """
    cookie_dict = {}
    for item in cookie_str.split(";"):
        if "=" in item:
            key, value = item.strip().split("=", 1)
            cookie_dict[key] = value
    return cookie_dict


def get_cookie_value(cookie_value, key: str, default: Optional[str] = None) -> Optional[str]:
    """
    从cookie中提取指定键的值
    参数:
    - key (str): 要提取的键名
    - default (Optional[str]): 默认值，如果键不存在则返回此值
    返回: - Optional[str]: 指定键的值，如果不存在则返回None或默认值
    """

    if isinstance(cookie_value, str):
        # 如果是字符串，转换为字典
        cookie_dict = cookie_str_to_dict(cookie_value)
    elif isinstance(cookie_value, dict):
        # 如果是字典，直接使用
        cookie_dict = cookie_value
    else:
        raise TypeError(f"不支持的cookie类型: {type(cookie_value)},期望str或dict类型")

    return cookie_dict.get(key, default)


def get_multiple_cookie_values(cookie_value, keys: List[str]) -> Dict[str, Optional[str]]:
    """
    从cookie中提取多个指定键的值
    参数:- keys (List[str]): 要提取的键名列表
    返回: - Dict[str, Optional[str]]: 包含键值对的字典
    """

    if isinstance(cookie_value, str):
        # 如果是字符串，转换为字典
        cookie_dict = cookie_str_to_dict(cookie_value)
    elif isinstance(cookie_value, dict):
        # 如果是字典，直接使用
        cookie_dict = cookie_value
    else:
        raise TypeError(f"不支持的cookie类型: {type(cookie_value)},期望str或dict类型")

    return {key: cookie_dict.get(key) for key in keys}


def get_new_cookie(cookie_str, _m_h5_tk, _m_h5_tk_enc, exclude_keys=None):
    """
    更新新的cookie

    该函数用于重组Cookie字符串，主要功能包括：
    1. 解析原始Cookie字符串为字典格式
    2. 根据过滤条件排除不需要的Cookie项
    3. 更新或添加特定的Token值（_m_h5_tk和_m_h5_tk_enc）
    4. 重新组合为标准Cookie字符串格式

    Args:
        cookie_str (str): 原始Cookie字符串
        _m_h5_tk (str): 新的_m_h5_tk值（通常是API请求中动态生成的token）
        _m_h5_tk_enc (str): 新的_m_h5_tk_enc值（与_m_h5_tk配对使用）
        exclude_keys (list): 需要过滤掉的Cookie键名列表，默认为空

    Returns:
        str: 重组后的Cookie字符串
    """
    cookie_dict = {}
    # 将 "key1=value1; key2=value2" 格式的字符串解析为字典
    for item in cookie_str.split(';'):
        # 去掉空格并分割键值对
        if '=' in item:
            key, value = item.strip().split('=', 1)
            if not exclude_keys:
                cookie_dict[key] = value
            else:
                # 如果提供了filter列表，则排除指定的键
                if key not in exclude_keys:
                    cookie_dict[key] = value
                else:
                    pass

    # 更新或添加特定的Token值
    if _m_h5_tk:
        cookie_dict['_m_h5_tk'] = _m_h5_tk
    if _m_h5_tk_enc:
        cookie_dict['_m_h5_tk_enc'] = _m_h5_tk_enc

    # 将字典重新组合为标准Cookie格式
    cookie_str = "; ".join([f"{key}={value}" for key, value in cookie_dict.items()])
    return cookie_str


if __name__ == '__main__':
    cookie = {"_samesite_flag_": "true", "cookie2": "1753486807965e06302fb095cdf2d919",  # noqa
              "t": "fb8fac7e872c4f2e00ed4c61d78dd674", "_tb_token_": "7e690358b5b76", "3PcFlag": "1754346259963",
              "xlly_s": "1", "unb": "2212151220659",  # noqa
              "sn": "%E6%9E%97%E5%86%85%E4%BC%81%E4%B8%9A%E5%BA%97%3A%E4%B8%80%E5%85%83",
              "uc1": "cookie14=UoYbz9iqGl1NIA%3D%3D&cookie21=URm48syIZx9a", "csg": "9cc1a9c0",
              "_cc_": "U%2BGCWk%2F7og%3D%3D", "cancelledSubSites": "empty", "skt": "1b54a68225524832",
              "sgcookie": "E100JgC9K7HSEIWFT1rUl35BYxie8K6zbkwmP8%2FJIfLJq1Zc1hb9MJiSVSSV28fpvwFwP9Kt33bSTkObmEQpzprX8HddxQwxHe5mWhzTQ9dlXQtkjhQex38mxXrkNN%2BQBPX5",
              # noqa
              "_m_h5_tk": "237c78352ffa35dad04b61fea1e4c28b_1754354571373",
              "_m_h5_tk_enc": "d2ee56020db282a5648554356a19e052", "_euacm_ac_l_uid_": "2212151220659",  # noqa
              "2212151220659_euacm_ac_c_uid_": "3830928885", "2212151220659_euacm_ac_rs_uid_": "3830928885",  # noqa
              "_portal_version_": "new", "cc_gray": "1", "XSRF-TOKEN": "9730d74f-e5cc-4e02-838e-f578a495a9fe",  # noqa
              "x_one_bi_token": "one-bi-55a0e9dd61994f1b94139127f0b75887-3830928885-2212151220659",
              "cna": "FCEYIRqZxUoCAXrgmQJHKXHY", "_euacm_ac_rs_sid_": "null",  # noqa
              "JSESSIONID": "654673CB30D5058E9F7EFE78B42DDA57",
              "tfstk": "gSmtHB96sBAMZWnTKA8hnswqetpHCeDN9fk5mSVGlXhKhAngSxN0DjhxM54X_lmx9xlUniYZiXBxOX3glmVmDOoKwijM_FkfDoqXZQxkqA7a0oOo1qX-_5yqdS935NZ0tQqXZQxh-9awsoG0p5NqvvNUHGs_Gj_IdRPQhiNjGWaQF8f_cjGbOywbHN1b1N_COWybcSGbcpHQT-EbGfJWMW6_ii3TIlhQKtefciiLBPTnCWsbLDeTW7MsXisfURUTNANe1RHn1yM4kmWVDyDszjyS11OTcve-EPn9wGVq_mUxxyLVEJujd4ubJdtsplFToDl6qBrtlfoY7VB2UvZsT4Pz5eRUpcmuk7zdOCMnp5a-kfAFc50-dXUox6juAYgLvgPjq0QyS_V8nN9ppZ745J-q9ZysZ0_gvJFkBnQVuyJUp7vppZ745JyLZddOuZzeL"}  # noqa
    x = get_multiple_cookie_values(cookie, ['_tb_token_', 'B'])
    print(x)
