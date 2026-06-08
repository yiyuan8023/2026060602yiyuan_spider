from date_utils import get_date, get_is_date
from extra.logger_ import logger

from database.utils import get_longest_values, get_ordered_keys, quote_identifier


class TableSchemaMixin:
    """表结构维护能力：自动建表、补字段和按字段值推断列类型。"""

    def _table_exists(self, table_name):
        try:
            sql = f"SELECT 1 FROM {quote_identifier(table_name)} LIMIT 1;"
            self.cursor.execute(sql)
            return True
        except Exception as e:
            logger.warning(f"【{table_name}】不存在: {e}")
            return False

    def _create_table(self, items, table_name, primary_key=None, uu_id=None, user=None):
        """按采集记录自动建表，字段类型用样本最长值保护宽度。"""
        if not items:
            return

        # 不只看第一行，避免后续更长 id、订单号、编码被建成过窄字段。
        sample_item = get_longest_values(items)
        columns = []
        keys = get_ordered_keys([sample_item])

        if primary_key:
            columns.append("`id` INT AUTO_INCREMENT UNIQUE")
        else:
            columns.append("`id` INT AUTO_INCREMENT PRIMARY KEY")

        for key in keys:
            if uu_id and key == "uu_id":
                continue
            column_type = self._infer_column_type(key, sample_item.get(key))
            column_sql = f"{quote_identifier(key)} {column_type}"
            if key == primary_key:
                column_sql += " PRIMARY KEY"
            columns.append(column_sql)

        if uu_id:
            columns.append("`uu_id` VARCHAR(36) UNIQUE")

        columns.append("`create_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        columns.append(
            "`update_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
        )

        if user:
            columns.append("`create_user` VARCHAR(50) DEFAULT NULL")
            columns.append("`update_user` VARCHAR(50) DEFAULT NULL")

        create_sql = f"CREATE TABLE {quote_identifier(table_name)} ({', '.join(columns)});"

        try:
            self.cursor.execute(create_sql)
            if user:
                self._create_triggers(table_name)
            self.connect.commit()
            logger.info(f"表 `{table_name}` 创建成功")
        except Exception as e:
            self.connect.rollback()
            logger.error(f"创建表 `{table_name}` 失败: {e}")
            raise

    def _check_and_update_table_structure(self, items, table_name):
        existing_columns = self._get_existing_columns(table_name)
        columns_to_add = [column for column in get_ordered_keys(items) if column not in existing_columns]

        if columns_to_add:
            # 平台字段经常增减，采集前自动补缺失字段，避免整批写入失败。
            alter_sql = self._build_alter_table_sql(table_name, columns_to_add, items)
            self.execute_sql(alter_sql)
            logger.info(f"表 {table_name} 已成功添加新字段: {columns_to_add}")

    def _get_existing_columns(self, table_name):
        sql = f"SHOW COLUMNS FROM {quote_identifier(table_name)};"
        results = self.execute_sql(sql, fetch=True)
        return {result[0] for result in results}

    def _build_alter_table_sql(self, table_name, columns_to_add, items):
        sample_item = get_longest_values(items)
        alter_parts = []
        for column in columns_to_add:
            column_type = self._infer_column_type(column, sample_item.get(column))
            comment = f"add_{get_date(date_format='%Y-%m-%d %H:%M:%S')}"
            alter_parts.append(
                f"ADD COLUMN {quote_identifier(column)} {column_type} COMMENT '{comment}'"
            )

        alter_sql = f"ALTER TABLE {quote_identifier(table_name)} {' ,'.join(alter_parts)};"
        logger.info(alter_sql)
        return alter_sql

    @staticmethod
    def _infer_column_type(key, value):
        """按字段名和值推断数据库类型，优先保护 id、key、订单号等文本标识。"""
        str_value = str(value) if value is not None else ""
        lower_key = str(key).lower()

        if get_is_date(value):
            return "DATE" if len(str_value) <= 10 else "DATETIME"

        if any(token in lower_key for token in ("id", "key", "编号", "订单号", "编码", "单号")):
            return f"VARCHAR({min(max(len(str_value) * 2, 50), 1000)})"

        if isinstance(value, (int, float)) and len(str_value) < 10:
            return "DOUBLE"

        if len(str_value) > 500:
            return "TEXT"

        return f"VARCHAR({min(max(len(str_value) * 2, 50), 1000)})"

    def _create_triggers(self, table_name):
        """为需要用户追踪的表创建插入/更新触发器，权限不足时不中断建表。"""
        quoted_table = quote_identifier(table_name)
        triggers = [
            (
                f"CREATE TRIGGER {quote_identifier(f'before_insert_{table_name}')} "
                f"BEFORE INSERT ON {quoted_table} FOR EACH ROW "
                "BEGIN SET NEW.create_user = USER(); END;"
            ),
            (
                f"CREATE TRIGGER {quote_identifier(f'before_update_{table_name}')} "
                f"BEFORE UPDATE ON {quoted_table} FOR EACH ROW "
                "BEGIN SET NEW.update_user = USER(); END;"
            ),
        ]

        for trigger_sql in triggers:
            try:
                self.cursor.execute(trigger_sql)
            except Exception as e:
                logger.warning(
                    f"表 `{table_name}`创建触发器失败（可能由于权限问题）: {e}"
                )

        self.connect.commit()
        logger.info(f"表 `{table_name}` 创建用户插入和更新触发器成功")
