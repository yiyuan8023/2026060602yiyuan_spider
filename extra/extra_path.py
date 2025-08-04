
from pathlib import Path
import inspect
from extra.logger_ import logger

def get_caller_file_name() -> str:
    # 获取当前函数的调用栈
    caller_frame = inspect.stack()[1]
    # 获取调用方的文件路径
    caller_file_path = caller_frame.filename
    # 获取调用方的文件名（不包括扩展名）
    p = Path(caller_file_path).stem
    logger.info(f"调用方的文件名称是：{p}")
    return p

if __name__ == '__main__':
    caller_file_name = get_caller_file_name()
    print(caller_file_name)
