# -*- coding: utf-8 -*-
# @Time : 2025/1/21 11:10
# @Author : Shao0000
# @Email : Shao0000@aliyun.com
# @File : logger_.py
# @Project : PyCharm
import sys
from functools import wraps
import os
import datetime
import loguru

# from settings import LOGFILE

# # 初始化一个空列表来存储错误信息
# error_logs = []
# error_logs2 = []
#
#
# def collect_error_logger(message):
#     if "cookie为空或者已失效" in message:
#         error_logs.append(message)
#         error_logs2.append(message)
#     else:
#         error_logs.append(message)


# 单例类的装饰器
def singleton_class_decorator(cls):
    """
    装饰器，单例类的装饰器
    """
    # 在装饰器里定义一个字典，用来存放类的实例。
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

    def get_project_path(self, project_path=None):
        if project_path is None:
            # 当前项目文件的，绝对真实路径
            # 路径，一个点代表当前目录，两个点代表当前目录的上级目录
            project_path = os.path.dirname(os.path.abspath(__file__))
        # 返回当前项目路径
        return project_path

    def get_log_path(self):
        # 项目目录
        project_path = self.get_project_path()
        # 项目日志目录
        project_log_dir = os.path.join(project_path, './log')
        # 日志文件名
        project_log_filename = 'jide{}.log'.format(datetime.date.today())
        # 日志文件路径
        project_log_path = os.path.join(project_log_dir, project_log_filename)
        # 返回日志路径
        return project_log_path

    def logger_add(self):
        LOGFILE=1
        if LOGFILE:
            loguru.logger.add(
                sink=self.get_log_path(),
                # 日志创建周期
                rotation='00:00',
                # 保存
                retention='1 year',
                # 文件的压缩格式
                compression='zip',
                # 编码格式
                encoding="utf-8",
                # 具有使日志记录调用非阻塞的优点
                enqueue=True,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {file}:{line} : {message}",
                level='INFO',
            )
        else:
            loguru.logger.add(sink=sys.stdout,format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {file}:{line} : {message}" ,level='INFO',)

        # 加了@property后，可以用调用属性的形式来调用方法,后面不需要加（）。
    @property
    def get_logger(self):
        return loguru.logger


'''
# 实例化日志类
'''

logger = Logger().get_logger
# logger.add(collect_error_logger, level="ERROR")
# if __name__ == '__main__':
#     logger.debug('调试代码')
#     logger.info('输出信息')
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