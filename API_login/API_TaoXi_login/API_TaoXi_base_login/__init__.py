"""淘系登录基础共用包：协议登录、Cookie管理、浏览器自动化。"""

from .havana import (
    configure_login,
    rsa_encrypt_password,
    extract_json_var,
    generate_page_trace_id,
    extract_security_tokens,
    get_security_tokens,
    login,
    login_with_retry,
    prepare_shop_cookie,
    BASE_HEADERS,
    TIMEOUT,
    DEFAULT_COOKIE_SITE,
    DEFAULT_COOKIE_URL,
    DEFAULT_COOKIE_DOMAIN,
    DEFAULT_COOKIE_MAX_AGE_DAYS,
    HAVANA_LOGIN_URL,
)
from .cookie_manager import (
    save_cookies_json,
    save_cookies_netscape,
    load_cookies_json,
    cookie_header_to_dict,
    browser_cookie_json_to_dict,
    merge_cookie_sources,
    cookie_dict_to_header,
    cookie_dict_to_browser_items,
    save_cookies_database,
    load_cookies_database,
    validate_cookies,
    validate_and_refresh_cookies,
)
from .browser_fallback import (
    is_verification_url,
    is_seller_logged_in_url,
    browser_login_fallback,
)
