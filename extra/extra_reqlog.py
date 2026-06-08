from sys import _getframe  # noqa
from typing import Optional

import requests
from extra.logger_ import logger


def _caller_text():
    """返回调用 req_log 的文件、函数和行号，便于从日志反查请求来源。"""
    frame = _getframe(2)
    return f"{frame.f_code.co_filename}:{frame.f_code.co_name}:{frame.f_lineno}"


def req_log(
    res: Optional[requests.Response],
    context: Optional[str] = None,
    raise_error: bool = False,
    log_success: bool = True,
):
    """
    针对 requests 响应统一打日志，默认返回 bool 供调用方判断是否继续解析。

    Args:
        res: requests 返回的 Response 对象。
        context: 安全的业务上下文，例如平台名、接口名、任务名。
        raise_error: True 时在失败响应上抛 HTTPError。
        log_success: False 时不记录成功日志，只记录失败日志。
    """

    # 自动带上调用位置，排查失败请求时能直接反查业务模块。
    caller = _caller_text()
    context_text = f"{context}，" if context else ""

    if res is None:
        message = f"{context_text}在{caller}发起了调用，请求响应为空"
        logger.error(message)
        if raise_error:
            raise requests.HTTPError(message)
        return False

    if 200 <= res.status_code < 300:
        if log_success:
            logger.info(
                f"{context_text}在{caller}发起了调用，请求成功"
                f"（status_code:{res.status_code}）"
            )
        return True

    reason = getattr(res, "reason", "")
    reason_text = f"，reason:{reason}" if reason else ""
    message = (
        f"{context_text}在{caller}发起了调用，请求失败"
        f"（status_code:{res.status_code}{reason_text}）"
    )
    logger.error(message)
    if raise_error:
        raise requests.HTTPError(message, response=res)
    return False


# 使用示例：
# 1. 普通请求，只打日志并返回 bool：
#    if req_log(response, context="拼多多商品明细"):
#        data = response.json()
#
# 2. 关键链路失败即中断：
#    req_log(response, context="光合mtop:download.task.status", raise_error=True)
#
# 3. 高频轮询只记录失败，避免成功日志刷屏：
#    req_log(response, context="任务状态轮询", log_success=False)
