import sys
from functools import wraps
import os
import datetime
import loguru

from extra.settings import LOGFILE


# 单例类的装饰器
def singleton_class_decorator(cls):
    """
    单例模式装饰器，确保类只有一个实例,防止日志类被多次实例化
    """

    # 在装饰器里定义字典，用来存放类的实例,
    _instance = {}

    # 装饰器，被装饰的类
    @wraps(cls)
    def wrapper_class(*args, **kwargs):
        # 判断，类实例不在类实例的字典里，就重新创建类实例
        if cls not in _instance:
            # 将新创建的类实例，存入到实例字典中
            _instance[cls] = cls(*args, **kwargs)
        # 如果实例字典中，存在类实例，直接取出返回类实例
        return _instance[cls]

    # 返回，装饰器中，被装饰的类函数
    return wrapper_class


@singleton_class_decorator
class Logger:
    def __init__(self):
        self.logger_add()

    @staticmethod
    def get_project_path(project_path=None):
        # 获取项目路径(父路径)
        if project_path is None:
            # 当前项目文件的，绝对真实路径
            # 路径，一个点代表当前目录，两个点代表当前目录的上级目录
            # C:\Users\admin\Desktop\yiyuan_spider
            project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            # 项目日志目录（新建log文件夹）
            project_log_dir = os.path.join(project_path, "log")
            # 返回当前项目路径
            return project_log_dir

    def get_log_path(self, filename=None):
        # 获取项目要保存的日志路径

        # 项目目录
        project_log_dir = self.get_project_path()
        # 日志文件名
        project_log_filename = f"{datetime.date.today()}_{filename}.log"
        # 日志文件路径
        project_log_path = os.path.join(project_log_dir, project_log_filename)
        # 返回日志路径
        return project_log_path

    def logger_add(self):
        # 配置日志输出
        # logfile = 1  # 开关变量，控制日志输出方式
        if LOGFILE:  # 开关变量，控制日志输出方式，setting中设置
            loguru.logger.add(
                # 日志文件的保存路径
                sink=self.get_log_path("yiyuan"),
                # 日志创建周期 - 每天00:00创建新日志文件
                rotation="00:00",
                # 保存策略 - 保留1年的日志文件
                retention="1 year",
                # 文件的压缩格式 - 超过保留期限的日志会压缩为zip格式
                compression="zip",
                # 编码格式
                encoding="utf-8",
                # 具有使日志记录调用非阻塞的优点 - 异步写入日志提高性能
                enqueue=True,
                # 日志格式 - 包含时间、级别、文件名、行号和消息内容
                format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {file}:{line} : {message}",
                # 日志级别 - 记录INFO级别及以上的日志
                level="INFO",
            )

            # 添加专门的错误日志文件
            loguru.logger.add(
                sink=self.get_log_path("yiyuan_error"),
                rotation="00:00",  # 每天轮转
                retention="1 year",
                compression="zip",
                encoding="utf-8",
                enqueue=True,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {file}:{line} : {message}",
                level="ERROR",  # 只记录ERROR及以上级别的日志
            )
        else:
            # 如果 logfile 为假值，则将日志输出到控制台
            loguru.logger.add(
                sink=sys.stdout,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {file}:{line} : {message}",
                level="INFO",
            )

        # 加了@property后，可以用调用属性的形式来调用方法,后面不需要加（）。

    @property
    def get_logger(self):
        # 获取日志对象
        return loguru.logger


# 初始化一个空列表来存储错误信息
error_logs = []
error_cookie_logs = []


def collect_error_logger(message):
    if "cookie为空或者已失效" in message:
        # 如果错误消息包含"cookie为空或者已失效"，则同时添加到两个列表中
        error_logs.append(message)
        error_cookie_logs.append(message)
    else:
        # 如果不是cookie相关的错误，则只添加到error_logs列表中
        error_logs.append(message)


# 实例化日志类
logger = Logger().get_logger

# 在模块加载时执行了，所以当你导入时，错误收集功能已经生效。
logger.add(collect_error_logger, level="ERROR")
# if __name__ == '__main__':
#     logger.debug('调试代码')
# #     logger.info('输出信息')
#     logger.success('输出成功')
#     logger.warning('错误警告')
#     logger.error('代码错误')
#     logger.critical('崩溃输出')
#
#     """
#     在其他.py文件中，只需要直接导入已经实例化的logger类即可
#     例如导入方式如下：
#     from .log_ import Logger, logger
#     然后直接使用logger即可
#     """
#     logger.info('----原始测试----')


# 你可以直接使用 logger 来记录日志
# logger.error("cookie为空或者已失效")  # 这会被添加到 error_logs 和 error_logs2
# logger.error("普通错误")  # 这只会被添加到 error_logs
#
# # 检查收集到的错误，可以发送邮件或者保存到数据库中
# print("所有错误:", error_logs)
# print("Cookie相关错误:", error_cookie_logs)

# if error_logs:
#     body = "".join(error_logs)
#     send_email(f"京东商智报错信息_{getTimeStr()}", body)
# if error_cookie_logs:
#     body = "".join(error_logs2)
#     h = str_html('“.*”', body)
#     send_email(f"京东商智报错信息_{getTimeStr()}", h, ['shuju_python@bi-cheng.cn'], 'html')
