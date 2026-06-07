"""
兼容旧入口。

新的数据库基础设施代码已迁移到 database 包，老脚本会逐步改为：
from database import DBManager
"""

from database import DBManager

__all__ = ["DBManager"]
