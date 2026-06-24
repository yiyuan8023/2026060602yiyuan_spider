"""DChain (Alibaba 供应链) 登录封装"""

from __future__ import annotations

import logging
import requests
from typing import Any
from urllib.parse import urlencode

from ..API_TaoXi_base_login import (
    prepare_shop_cookie,
    configure_login,
    load_cookies_database,
    merge_cookie_sources,
    validate_and_refresh_cookies,
    save_cookies_database,
    cookie_dict_to_header,
)
from ..API_TaoXi_base_login.havana import BASE_HEADERS, TIMEOUT

log = logging.getLogger("dchain_login")

SITE = "DChain"
VALIDATE_URL = "https://web.scm.tmall.com/"

HAVANA_LOGIN_URL = (
    "https://havanalogin.taobao.com/mini_login.htm?"
    + urlencode({
        "lang": "zh_CN",
        "appName": "ascp",
        "appEntrance": "ascp_default",
        "styleType": "auto",
        "bizParams": "",
        "notLoadSsoView": "true",
        "notKeepLogin": "false",
        "isMobile": "false",
        "returnUrl": "https://web.scm.tmall.com/login",
        "qrCodeFirst": "false",
    })
)


def _dchain_st_callback(session: requests.Session, st: str, st2: str, return_url: str) -> None:
    from ..API_TaoXi_base_login import havana
    _timeout = havana.TIMEOUT

    proxy_url = f"https://web.scm.tmall.com/pages/ascm/basic_login_proxy?action=login&st={st}&st2={st2}"
    log.info(f"  DChain proxy: {proxy_url[:80]}...")
    try:
        session.get(proxy_url, timeout=_timeout)
    except Exception as exc:
        log.warning(f"  basic_login_proxy 失败: {exc}")
        return
    try:
        session.post("https://session.scm.tmall.com/session/updateSession", timeout=_timeout)
    except Exception as exc:
        log.warning(f"  updateSession 失败: {exc}")
    try:
        session.get("https://scm.tmall.com/basic/autoLogin?locale=zh-cn", timeout=_timeout)
    except Exception as exc:
        log.warning(f"  autoLogin 失败: {exc}")


def prepare_dchain_cookie(
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
        st_callback=_dchain_st_callback,
        **login_options,
    )
