import os

# 条件：os.environ.get("MYSQL_DBNAME") （检查环境变量是否存在）
# 如果条件为真（环境变量存在且不为空）：使用环境变量的值
# 如果条件为假（环境变量不存在或为空）：使用默认值 "yiyuan_test" # noqa

MYSQL_HOST = "223.5.242.173"
MYSQL_DBNAME = os.environ.get("MYSQL_DBNAME") if os.environ.get("MYSQL_DBNAME") else "yiyuan_test"  # noqa
MYSQL_USER = "bc_yiyuan_test"  # noqa
MYSQL_PASSWORD = "yiyuan12345678"  # noqa
MYSQL_PORT = 3306

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"  # noqa
