import pymysql

from config import get_database_config
from extra.logger_ import logger

from database.repositories import CookieRepositoryMixin
from database.schema import TableSchemaMixin
from database.writer import DataWriterMixin


class DBManager(CookieRepositoryMixin, DataWriterMixin, TableSchemaMixin):
    def __init__(self, db_config=None):
        db_params = get_database_config(db_config)
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
