"""淘宝会员登录封装（适用于DChain的"淘宝登录"tab）"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from ..API_TaoXi_base_login import (
    prepare_shop_cookie,
    configure_login,
)
from extra.logger_ import logger

SITE = "TaobaoMember"
VALIDATE_URL = "https://www.taobao.com/"  # 淘宝主站

# 淘宝会员登录入口（iframe src）
HAVANA_LOGIN_URL = (
    "https://login.taobao.com/member/login.jhtml?"
    + urlencode({
        "style": "miniall",
        "sub": "true",
        "sub_jump": "current_url",
    })
)


def prepare_taobao_member_cookie(
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
    淘宝会员登录Cookie准备（用于DChain的"淘宝登录"tab）

    这个登录方式使用Havana系统，但appName=taobao（而不是ascp）。
    适用于必须通过"淘宝登录"tab才能登录的DChain账号。

    参数:
        shop_name: 店铺名称（用于日志）
        login_id: 登录账号
        password: 登录密码
        db_cookie_str/db_cookie: 数据库Cookie
        site: 站点标识
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
        st_callback=None,  # 淘宝会员登录不需要特殊的ST回调
        **login_options,
    )
