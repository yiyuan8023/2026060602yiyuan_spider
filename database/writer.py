import uuid

from extra.extra_date import get_date
from extra.logger_ import logger

from database.utils import clean_db_value, get_ordered_keys, quote_identifier


class DataWriterMixin:
    def update_insert_data(
        self,
        items,
        table_name,
        primary_key=None,
        uu_id=None,
        user=None,
        batch_size=5000,
    ):
        if not items:
            return

        if uu_id:
            for item in items:
                item.setdefault("uu_id", str(uuid.uuid4()))

        if not self._table_exists(table_name):
            logger.info(f"表 {table_name} 不存在，开始创建表...")
            self._create_table(items, table_name, primary_key, uu_id, user)
        else:
            self._check_and_update_table_structure(items, table_name)

        field_names = get_ordered_keys(items)
        fields_str = ", ".join(quote_identifier(field) for field in field_names)
        update_fields = [field for field in field_names if field not in ["created_at", "create_time"]]
        duplicate_str = ",".join(
            f"{quote_identifier(field)}=VALUES({quote_identifier(field)})"
            for field in update_fields
        )

        placeholders = ", ".join(["%s"] * len(field_names))
        insert_sql = (
            f"INSERT INTO {quote_identifier(table_name)}({fields_str}) VALUES ({placeholders}) "
            f"ON DUPLICATE KEY UPDATE {duplicate_str};"
        )

        total_items = len(items)
        logger.info(
            f"总共 {total_items} 条数据，开始时间：{get_date(date_format='%Y-%m-%d %H:%M:%S')}"
        )

        for i in range(0, total_items, batch_size):
            batch_items = items[i : i + batch_size]
            values_tuples = [
                tuple(self._normalize_value(item.get(field)) for field in field_names)
                for item in batch_items
            ]

            try:
                self.cursor.executemany(insert_sql, values_tuples)
                self.connect.commit()
                logger.info(
                    f"已处理 {min(i + batch_size, total_items)}/{total_items} 条数据"
                )
            except Exception as e:
                self.connect.rollback()
                logger.error(f"执行 SQL 语句时发生错误: {e}")
                raise

        logger.info(f"结束时间：{get_date(date_format='%Y-%m-%d %H:%M:%S')}")

    @staticmethod
    def _normalize_value(value):
        value = clean_db_value(value)
        if value is None:
            return None
        if isinstance(value, str) and value == "":
            return None
        return value

    def insert_delete_insert_data(
        self, items, db_table_name, del_sql, uu_id=None, user=None
    ):
        if not items:
            logger.warning("没有需要插入的数据")
            return False

        try:
            table_exists = self._table_exists(db_table_name)
            logger.info(
                f"表 {db_table_name} {'存在,测试写入数据' if table_exists else '不存在,跳过先删后入操作,直接创建表'}"
            )

            if table_exists:
                logger.info(f"开始测试插入2条数据到表 {db_table_name}")
                self.update_insert_data(
                    items[:2], db_table_name, primary_key=None, uu_id=uu_id, user=user
                )
                logger.info(f"{db_table_name}测试插入成功")

                logger.info("开始删除指定条件的数据")
                self.execute_sql(del_sql)
                logger.info(f"删除成功，已执行【{del_sql}】")

            logger.info("准备批量写入数据")
            self.update_insert_data(
                items, db_table_name, primary_key=None, uu_id=uu_id, user=user
            )
            logger.info("批量插入完成")
            self.close()
            return True

        except Exception as e:
            self.close()
            logger.error(f"数据更新失败: {e}")
            raise
