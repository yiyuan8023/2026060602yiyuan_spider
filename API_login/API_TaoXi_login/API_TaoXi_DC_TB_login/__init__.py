"""DChain淘宝登录封装（适用于DChain的"淘宝登录"tab）"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from ..API_TaoXi_base_login import prepare_shop_cookie
from extra.logger_ import logger

SITE = "DChain_TB"
VALIDATE_URL = "https://web.scm.tmall.com/"  # DChain站点

# 淘宝会员登录入口（DChain "淘宝登录"tab对应的iframe）
# 使用mini_login.htm iframe方式，appName=taobao，returnUrl指向DChain
HAVANA_LOGIN_URL = (
    "https://havanalogin.taobao.com/mini_login.htm?"
    + urlencode({
        "lang": "zh_CN",
        "appName": "taobao",
        "appEntrance": "default",
        "styleType": "auto",
        "bizParams": "",
        "notLoadSsoView": "true",
        "notKeepLogin": "false",
        "isMobile": "false",
        "returnUrl": "https://web.scm.tmall.com/login",
        "qrCodeFirst": "false",
    })
)


def _dchain_tb_st_callback(session, st: str, st2: str, return_url: str) -> None:
    """
    DChain淘宝登录的ST回调（与普通DChain登录相同）
    登录成功后需要执行DChain的4步session建立流程
    """
    from ..API_TaoXi_DC_login import _dchain_st_callback
    _dchain_st_callback(session, st, st2, return_url)


def prepare_dchain_tb_cookie(
    shop_name: str,
    login_id: str | None = None,
    password: str | None = None,
    db_cookie_str: str | None = None,
    db_cookie: str | dict | list | None = None,
    site: str = SITE,
    save_local: bool = False,
    **login_options,
) -> dict[str, Any]:
    """
    DChain淘宝登录Cookie准备（用于必须通过"淘宝登录"tab才能登录的DChain账号）

    这个登录方式使用Havana系统，但appName=taobao（而不是ascp）。
    登录成功后仍然需要执行DChain的4步ST回调建立session。

    适用场景：
    - 某些DChain账号（如林内供应商:BI）必须点击"淘宝登录"tab才能登录
    - 点击"普通登录"tab会持续返回"请输入密码"

    参数:
        shop_name: 店铺名称（用于日志）
        login_id: 登录账号
        password: 登录密码
        db_cookie_str/db_cookie: 数据库Cookie
        site: 站点标识（默认DChain_TB）
        save_local: 是否保存本地文件
        **login_options: 其他登录选项

    返回:
        {"status": "success/error/...", "cookies": {...}, "message": "..."}
    """
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
        st_callback=_dchain_tb_st_callback,  # 使用DChain的ST回调
        **login_options,
    )
