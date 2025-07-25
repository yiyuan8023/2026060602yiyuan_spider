import os

# 条件：os.environ.get("MYSQL_DBNAME") （检查环境变量是否存在）
# 如果条件为真（环境变量存在且不为空）：使用环境变量的值
# 如果条件为假（环境变量不存在或为空）：使用默认值 "jide_test"

MYSQL_HOST = "223.5.242.173"
MYSQL_DBNAME = os.environ.get("MYSQL_DBNAME") if os.environ.get("MYSQL_DBNAME") else "yiyuan_test"
MYSQL_USER = "bc_yiyuan_test"
MYSQL_PASSWORD = "yiyuan12345678"
MYSQL_PORT = 3306
