import datetime
import os
import sys
from collections import deque
from functools import wraps

from loguru import logger as loguru_logger

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import LOG_MODE


LOG_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss} | {level} | "
    "{file}:{function}:{line} : {message}"
)
MAX_ERROR_LOGS = 1000


def singleton_class_decorator(cls):
    """单例类装饰器，避免日志配置在同一进程内重复初始化。"""
    _instance = {}

    @wraps(cls)
    def wrapper_class(*args, **kwargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)
        return _instance[cls]

    return wrapper_class


@singleton_class_decorator
class Logger:
    """项目统一日志入口，根据 LOG_MODE 配置文件、控制台或双通道输出。"""

    def __init__(self):
        self.logger_add()

    @staticmethod
    def get_project_path(project_path=None):
        """返回项目 log 目录；目录不存在时自动创建。"""
        base_path = project_path or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_log_dir = os.path.join(base_path, "log")
        os.makedirs(project_log_dir, exist_ok=True)
        return project_log_dir

    def get_log_path(self, filename=None):
        """按当前日期生成日志文件路径。"""
        project_log_dir = self.get_project_path()
        safe_filename = filename or "yiyuan"
        project_log_filename = f"{datetime.date.today()}_{safe_filename}.log"
        return os.path.join(project_log_dir, project_log_filename)

    def _add_file_sinks(self):
        """添加普通日志和错误日志两个文件输出。"""
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

    @staticmethod
    def _add_console_sink():
        """添加控制台输出，主要用于本地调试。"""
        loguru_logger.add(
            sink=sys.stdout,
            format=LOG_FORMAT,
            level="INFO",
        )

    def logger_add(self):
        """按 LOG_MODE 初始化日志通道：file、console、both。"""
        loguru_logger.remove()

        if LOG_MODE in {"file", "both"}:
            self._add_file_sinks()
        if LOG_MODE in {"console", "both"}:
            self._add_console_sink()

    @property
    def get_logger(self):
        return loguru_logger


# 长时间跑调度器时限制内存占用，仍兼容 append / join 等常见用法。
error_logs = deque(maxlen=MAX_ERROR_LOGS)
error_cookie_logs = deque(maxlen=MAX_ERROR_LOGS)


def _is_cookie_error(message_text):
    """识别常见 Cookie 失效文案，用于后续通知分类。"""
    lower_message = message_text.lower()
    if "cookie" not in lower_message:
        return False
    return any(
        keyword in lower_message
        for keyword in ("为空", "失效", "过期", "没有cookie", "expired", "invalid")
    )


def collect_error_logger(message):
    """收集 ERROR 级别纯文本消息，供邮件、钉钉或调度器汇总使用。"""
    message_text = message.record.get("message", str(message))
    error_logs.append(message_text)
    if _is_cookie_error(message_text):
        error_cookie_logs.append(message_text)


logger = Logger().get_logger

# 错误收集 sink 只记录纯消息，便于后续邮件、钉钉或调度器统一处理。
logger.add(collect_error_logger, level="ERROR")


if __name__ == "__main__":
    """
    使用示例：

    1. 普通业务代码直接导入：
       from extra.logger_ import logger
       logger.info("开始采集")

    2. 最终执行脚本临时切换日志模式，必须在导入 logger 前设置：
       import os
       os.environ["LOG_MODE"] = "both"  # file / console / both
       from extra.logger_ import logger

    3. 错误汇总通知可以消费 error_logs：
       from extra.logger_ import error_logs, error_cookie_logs
       body = "\\n".join(error_logs)
    """
    logger.info(f"当前日志模式: {LOG_MODE}")
    logger.info("普通进度日志示例")
    logger.warning("可恢复问题日志示例")
    logger.error("cookie为空或者已失效")
    print(f"错误日志数量: {len(error_logs)}")
    print(f"Cookie错误数量: {len(error_cookie_logs)}")
