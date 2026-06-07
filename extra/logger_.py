import datetime
import os
import sys
from collections import deque
from functools import wraps

from loguru import logger as loguru_logger
from extra.settings import LOGFILE


LOG_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss} | {level} | "
    "{file}:{function}:{line} : {message}"
)
MAX_ERROR_LOGS = 1000


# 单例类的装饰器，避免日志配置在同一进程内重复初始化。
def singleton_class_decorator(cls):
    _instance = {}

    @wraps(cls)
    def wrapper_class(*args, **kwargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)
        return _instance[cls]

    return wrapper_class


@singleton_class_decorator
class Logger:
    def __init__(self):
        self.logger_add()

    @staticmethod
    def get_project_path(project_path=None):
        base_path = project_path or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_log_dir = os.path.join(base_path, "log")
        os.makedirs(project_log_dir, exist_ok=True)
        return project_log_dir

    def get_log_path(self, filename=None):
        project_log_dir = self.get_project_path()
        safe_filename = filename or "yiyuan"
        project_log_filename = f"{datetime.date.today()}_{safe_filename}.log"
        return os.path.join(project_log_dir, project_log_filename)

    def logger_add(self):
        loguru_logger.remove()

        if LOGFILE:
            loguru_logger.add(
                sink=self.get_log_path("yiyuan"),
                rotation="00:00",
                retention="1 year",
                compression="zip",
                encoding="utf-8",
                enqueue=True,
                format=LOG_FORMAT,
                level="INFO",
            )

            loguru_logger.add(
                sink=self.get_log_path("yiyuan_error"),
                rotation="00:00",
                retention="1 year",
                compression="zip",
                encoding="utf-8",
                enqueue=True,
                format=LOG_FORMAT,
                level="ERROR",
            )
        else:
            loguru_logger.add(
                sink=sys.stdout,
                format=LOG_FORMAT,
                level="INFO",
            )

    @property
    def get_logger(self):
        return loguru_logger


# 长时间跑调度器时限制内存占用，仍兼容 append / join 等常见用法。
error_logs = deque(maxlen=MAX_ERROR_LOGS)
error_cookie_logs = deque(maxlen=MAX_ERROR_LOGS)


def _is_cookie_error(message_text):
    lower_message = message_text.lower()
    if "cookie" not in lower_message:
        return False
    return any(
        keyword in lower_message
        for keyword in ("为空", "失效", "过期", "没有cookie", "expired", "invalid")
    )


def collect_error_logger(message):
    message_text = message.record.get("message", str(message))
    error_logs.append(message_text)
    if _is_cookie_error(message_text):
        error_cookie_logs.append(message_text)


logger = Logger().get_logger

# 错误收集 sink 只记录纯消息，便于后续邮件、钉钉或调度器统一处理。
logger.add(collect_error_logger, level="ERROR")
