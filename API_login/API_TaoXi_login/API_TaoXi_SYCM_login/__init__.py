"""生意参谋 (SYCM) 登录封装"""

from __future__ import annotations

from typing import Any

from ..API_TaoXi_base_login import prepare_shop_cookie, cookie_dict_to_header
from ..API_TaoXi_base_login.havana import (
    DEFAULT_COOKIE_SITE,
    DEFAULT_COOKIE_URL,
    DEFAULT_COOKIE_DOMAIN,
)

SITE = DEFAULT_COOKIE_SITE  # "生意参谋"
VALIDATE_URL = "https://myseller.taobao.com/home.htm"
HAVANA_LOGIN_URL = "https://login.taobao.com/havanaone/login/login.htm?bizName=taobao"


def prepare_sycm_cookie(
    shop_name: str,
    login_id: str | None = None,
    password: str | None = None,
    db_cookie_str: str | None = None,
    db_cookie: str | dict | list | None = None,
    site: str = SITE,
    save_local: bool = False,
    **login_options,
) -> dict[str, Any]:
    login_options.setdefault("validate_url", VALIDATE_URL)
    login_options.setdefault("havana_login_url", HAVANA_LOGIN_URL)
    return prepare_shop_cookie(
        shop_name=shop_name,
        login_id=login_id,
        password=password,
        db_cookie_str=db_cookie_str,
        db_cookie=db_cookie,
        site=site,
        save_local=save_local,
        st_callback=None,
        **login_options,
    )
