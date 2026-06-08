import os

from config.local_config import get_local_section

DEFAULT_DATABASE_NAMES = {
    "test": "yiyuan_test",
    "rinnai_py": "rinnai_py", # noqa
    "caiwu_hzbc": "caiwu_hzbc", # noqa
    "rinnai": "rinnai", # noqa
    "rinnai_import": "rinnai",
    "jingdong": "bc",
    "jd_import": "project",
    "bc": "bc",
    "hb": "hb",
}


def _env_prefix(config_name):
    return "".join(
        char.upper() if char.isalnum() else "_"
        for char in str(config_name)
    )


def _env_value(config_name, key):
    specific_key = f"MYSQL_{_env_prefix(config_name)}_{key}"
    return os.environ.get(specific_key) or os.environ.get(f"MYSQL_{key}")


def _local_database_value(config_name, key):
    mysql_config = get_local_section("mysql")
    local_config = mysql_config.get(config_name, {})
    if not isinstance(local_config, dict):
        raise RuntimeError(f"本地数据库配置 {config_name} 必须是对象。")
    value = local_config.get(key.lower())
    return value if value not in {None, ""} else None


def _config_value(config_name, key):
    return _local_database_value(config_name, key) or _env_value(config_name, key)


def get_database_config(config_name=None, require_credentials=True):
    name = config_name or os.environ.get("MYSQL_CONFIG_NAME") or "test"
    config = {
        "host": _config_value(name, "HOST"),
        "db": _config_value(name, "DB") or DEFAULT_DATABASE_NAMES.get(name),
        "user": _config_value(name, "USER"),
        "password": _config_value(name, "PASSWORD"),
        "port": int(_config_value(name, "PORT") or 3306),
    }
    required_keys = ["host", "db", "port"]
    if require_credentials:
        required_keys.extend(["user", "password"])
    missing_keys = [key for key in required_keys if config.get(key) in {None, ""}]
    if missing_keys:
        env_prefix = f"MYSQL_{_env_prefix(name)}_"
        missing = ", ".join(missing_keys)
        raise RuntimeError(
            f"数据库配置 {name} 缺少字段: {missing}。"
            f"请在 config/local.json 中配置 mysql.{name}，"
            f"或配置 MYSQL_* / {env_prefix}* 环境变量。"
        )
    return config
