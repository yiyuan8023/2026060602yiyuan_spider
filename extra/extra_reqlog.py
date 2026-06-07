from sys import _getframe  # noqa
from typing import Optional

import requests
from extra.logger_ import logger


def _caller_text():
    frame = _getframe(2)
    return f"{frame.f_code.co_filename}:{frame.f_code.co_name}:{frame.f_lineno}"


def req_log(
    res: requests.models.Response,
    context: Optional[str] = None,
    raise_error: bool = False,
):
    """
    针对 requests 响应统一打日志。
    raise_error=True 时在非 2xx 响应上抛 HTTPError。
    """

    caller = _caller_text()
    context_text = f"{context}，" if context else ""

    if res is None:
        message = f"{context_text}在{caller}发起了调用，请求响应为空"
        logger.error(message)
        if raise_error:
            raise requests.HTTPError(message)
        return False

    if 200 <= res.status_code < 300:
        logger.info(
            f"{context_text}在{caller}发起了调用，请求成功（status_code:{res.status_code}）"
        )
        return True

    message = (
        f"{context_text}在{caller}发起了调用，请求失败"
        f"（status_code:{res.status_code}）"
    )
    logger.error(message)
    if raise_error:
        raise requests.HTTPError(message, response=res)
    return False
