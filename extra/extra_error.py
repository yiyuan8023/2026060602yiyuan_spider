import pandas as pd
import requests

from extra.logger_ import logger


def handle_request_error(error, context="请求"):
    """
    统一处理网络请求和数据处理过程中的异常
    Args:
        error (Exception): 捕获到的异常对象
        context (str): 错误上下文描述，默认为"请求"
    Returns:
        None
    """
    if isinstance(error, requests.exceptions.Timeout):
        logger.error(f"{context}超时: {str(error)}")
    elif isinstance(error, requests.exceptions.ConnectionError):
        logger.error(f"{context}连接错误: {str(error)}")
    elif isinstance(error, requests.exceptions.HTTPError):
        logger.error(f"{context}HTTP错误: {str(error)}")
    elif isinstance(error, requests.exceptions.RequestException):
        logger.error(f"{context}网络失败: {str(error)}")
    elif isinstance(error, pd.errors.EmptyDataError):
        logger.error(f"{context}数据为空或格式不正确: {str(error)}")
    elif isinstance(error, pd.errors.ParserError):
        logger.error(f"{context}数据解析错误: {str(error)}")
    elif isinstance(error, FileNotFoundError):
        logger.error(f"{context}文件未找到: {str(error)}")
    elif isinstance(error, IOError):
        logger.error(f"{context}文件读写错误: {str(error)}")
    elif isinstance(error, ValueError):
        logger.error(f"{context}数据解析错误: {str(error)}")
    else:
        logger.error(f"处理{context}时发生未知错误: {str(error)}")
        logger.error(f"错误类型: {type(error).__name__}")

    return None
