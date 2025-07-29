
import http.cookiejar


def cookiejar_to_cookie_str(cookie_jar) -> str:
    """
    将 http.cookiejar.CookieJar 对象转换为标准的 Cookie 字符串。

    :param cookie_jar: CookieJar 对象
    :return: Cookie 字符串，如 'key1=value1; key2=value2'
    """
    cookies = {}
    for cookie in cookie_jar:
        cookies[cookie["name"]] =cookie["value"]
    return "; ".join([f"{name}={value}" for name, value in cookies.items()])