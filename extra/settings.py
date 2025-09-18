import os

# 条件：os.environ.get("MYSQL_DBNAME") （检查环境变量是否存在）
# 如果条件为真（环境变量存在且不为空）：使用环境变量的值
# 如果条件为假（环境变量不存在或为空）：使用默认值 "yiyuan_test" # noqa

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"  # noqa


# 预定义的数据库配置
DATABASE_CONFIGS = {
    "test": {
        "host": "223.5.242.173",
        "db": os.environ.get("MYSQL_DBNAME") if os.environ.get("MYSQL_DBNAME") else "yiyuan_test",  # noqa,
        "user": "bc_yiyuan_test", # noqa,
        "password": "yiyuan12345678", # noqa,
        "port": 3306
    },
    "rinnai_py":  # noqa
        {
        "host": "223.5.242.173",
        "db": "rinnai_py", # noqa
        "user": "bc_yiyuan", # noqa
        "password": "yy123456",
        "port": 3306
        },
    "caiwu_hzbc":  # noqa
        {
            "host": "223.5.242.173",
            "db": "caiwu_hzbc",  # noqa
            "user": "bc_yiyuan",  # noqa
            "password": "yy123456",
            "port": 3306
        },
    "rinnai":  # noqa
        {
            "host": "223.5.242.173",
            "db": "rinnai",  # noqa
            "user": "bc_yiyuan",  # noqa
            "password": "yy123456",
            "port": 3306
        },
    "bc":  # noqa
        {
            "host": "223.5.242.173",
            "db": "bc",  # noqa
            "user": "bc_yiyuan",  # noqa
            "password": "yy123456",
            "port": 3306
        },
}
