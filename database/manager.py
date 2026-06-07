import pymysql

from extra.logger_ import logger
from extra.settings import DATABASE_CONFIGS

from database.repositories import CookieRepositoryMixin
from database.schema import TableSchemaMixin
from database.writer import DataWriterMixin


class DBManager(CookieRepositoryMixin, DataWriterMixin, TableSchemaMixin):
    def __init__(self, db_config=None):
        config_name = db_config or "test"
        db_params = DATABASE_CONFIGS.get(config_name)
        if not db_params:
            raise ValueError(f"未知数据库配置: {config_name}")

        db_params = dict(db_params)
        db_params.setdefault("charset", "utf8mb4")
        db_params.setdefault("autocommit", False)

        self.connect = pymysql.connect(**db_params)
        self.cursor = self.connect.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()

    def execute_sql(self, sql, params=None, fetch=False):
        try:
            self.cursor.execute(sql, params)
            if fetch:
                return self.cursor.fetchall()

            self.connect.commit()
            return None
        except Exception as e:
            if not fetch:
                self.connect.rollback()
            logger.error(f"执行 SQL 失败: {e}")
            raise

    def close(self):
        if getattr(self, "cursor", None):
            self.cursor.close()
            self.cursor = None
        if getattr(self, "connect", None):
            self.connect.close()
            self.connect = None
