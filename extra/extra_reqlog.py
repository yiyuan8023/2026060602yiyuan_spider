
from sys import _getframe # noqa
import requests
from extra.logger_ import logger


def req_log(res: requests.models.Response):
    """
    针对request请求的response对象的日志，通配
    """
    if res.status_code == 200:
        logger.info(f"在{_getframe(1)}发起了调用,请求成功（status_code:{res.status_code}）")
        return True
    else:
        logger.error(f"在{_getframe(1)}发起了调用,请求失败（status_code:{res.status_code}）")
        return False
