"""DChain (Alibaba 供应链) 登录封装"""

from __future__ import annotations

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
from extra.logger_ import logger

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

    # Step 1: basic_login_proxy 建立初始认证
    proxy_url = f"https://web.scm.tmall.com/pages/ascm/basic_login_proxy?action=login&st={st}&st2={st2}"
    logger.info(f"  DChain proxy: {proxy_url[:80]}...")
    try:
        session.get(proxy_url, timeout=_timeout)
    except Exception as exc:
        logger.warning(f"  basic_login_proxy 失败: {exc}")
        return

    # Step 2: 查询 tenants 获取 merchantCode
    mcode1 = ""
    mcode2 = ""
    merchant_type = ""
    try:
        resp = session.get(
            "https://permission-o.scm.tmall.com/views/tenants?_tag=default",
            timeout=_timeout,
        )
        if resp.status_code == 200:
            tenants_data = resp.json()
            tenants = tenants_data if isinstance(tenants_data, list) else tenants_data.get("data", [])
            if tenants and isinstance(tenants, list):
                tenant = tenants[0] if isinstance(tenants[0], dict) else {}
                mcode1 = tenant.get("merchantCode", "") or tenant.get("code", "")
                mcode2 = tenant.get("shortCode", "") or tenant.get("merchantShortCode", "")
                merchant_type = str(tenant.get("merchantType", ""))
                logger.info(f"  DChain tenants: mcode1={mcode1}, mcode2={mcode2}, type={merchant_type}")
    except Exception as exc:
        logger.warning(f"  tenants 查询失败: {exc}")

    # Step 3: updateSession
    try:
        session.post("https://session.scm.tmall.com/session/updateSession", timeout=_timeout)
    except Exception as exc:
        logger.warning(f"  updateSession 失败: {exc}")

    # Step 4: autoLogin 带商家参数
    auto_login_params = {"locale": "zh-cn"}
    if mcode1:
        auto_login_params["_mcode1_"] = mcode1
    if mcode2:
        auto_login_params["_mcode2_"] = mcode2
    if merchant_type:
        auto_login_params["merchantType"] = merchant_type
    auto_login_url = f"https://scm.tmall.com/basic/autoLogin?{urlencode(auto_login_params)}"
    logger.info(f"  DChain autoLogin: {auto_login_url[:100]}...")
    try:
        session.get(auto_login_url, timeout=_timeout)
    except Exception as exc:
        logger.warning(f"  autoLogin 失败: {exc}")


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
