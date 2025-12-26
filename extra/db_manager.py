"""
execute_sql:执行SQL语句
select_cookies_shop:根据站点和店铺名称查询cookie信息
select_cookies_all:根据站点查询所有店铺的cookie信息
update_insert_date：新增或更新数据，如果表不存在则自动创建
insert_delete_insert_data：执行"先测试插入、再删除历史数据、最后批量插入"的数据操作流程
_create_table：根据数据自动创建表
_check_and_update_table_structure：检查表结构是否需要更新，并自动添加新字段
_build_alter_table_sql:构建更新字段名称的SQL语句
_create_triggers:为指定表创建自动设置用户信息的触发器

close:关闭数据库连接和游标
"""
import re
import uuid
import pymysql
from pymysql.converters import escape_string

from extra.extra_date import get_date, get_is_date
from extra.extra_items import get_long_values
from extra.settings import *
from extra.logger_ import logger


# 添加mysql语言注释
# noinspection SqlDialectInspection,SqlNoDataSourceInspection
class DBManager:
    def __init__(self, db_config=None):
        if db_config is None:
            db_params = DATABASE_CONFIGS.get('test')
        else:
            db_params = DATABASE_CONFIGS.get(db_config)

        self.connect = pymysql.connect(**db_params)
        self.cursor = self.connect.cursor()

    def execute_sql(self, sql, fetch=False):
        """
        执行SQL语句
        :param sql: SQL语句
        :param fetch: 是否获取查询结果（仅适用于SELECT语句）
        :return: 查询结果（如果fetch=True）或None
        """
        self.cursor.execute(sql)

        if fetch:
            results = self.cursor.fetchall()
            self.connect.commit()
            return results
        else:
            self.connect.commit()
            return None

    def select_cookies_shop(self, site: str, shop_names: str):

        sql = f"""select `店铺名称`,`cookie_str`,`cookie`  from `cookie` 
                    where  `站点`='{site}' and `店铺名称` in {shop_names};"""
        return self.execute_sql(sql, fetch=True)

    def select_cookies_all(self, site: str):

        sql = f"select `店铺名称`,`cookie_str`,`cookie`  from `cookie` where  `站点`='{site}';"
        return self.execute_sql(sql, fetch=True)

    def update_insert_date(self, items, table_name, primary_key=None, uu_id=None, user=None):
        """
        新增或更新数据，如果表不存在则自动创建
        :param items: 要插入的数据列表，每个元素是一个字典
        :param table_name: 目标表名
        :param primary_key: 主键字段名，默认为数据中的第一个字段
        :param uu_id: 是否为每条记录添加 UUID 字段（默认不添加）
        :param user:是否添加更新用户触发器
        :return:
        """
        if not items:
            return

        # 检查表是否存在，如果不存在则创建
        if not self._table_exists(table_name):
            self._create_table(items, table_name, primary_key, uu_id, user)
        else:
            # 检查并更新表结构
            self._check_and_update_table_structure(items, table_name)

        # 为每个数据项添加UUID（如果不存在）
        for item in items:
            if 'uu_id' not in item and uu_id:
                item['uu_id'] = str(uuid.uuid4())

        # 获取字段名列表（从第一条记录）
        field_names = list(items[0].keys())

        # 构建字段名字符串
        fields_str = ", ".join([f"`{field}`" for field in field_names])

        # 构建所有记录的值字符串
        values_list = []
        for item in items:  # 遍历每个数据字典
            values = []
            for field in field_names:  # 按照统一的字段顺序处理值
                value = item.get(field)  # 使用get方法避免KeyError

                # 添加剔除首尾空格和不可见字符的处理
                if isinstance(value, str):
                    # 去除首尾空格并移除不可见字符（包括制表符、换行符等）
                    value = value.strip()
                    # 使用正则表达式移除所有不可见字符
                    value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)

                if not value:  # 如果值为空
                    values.append("NULL")
                elif isinstance(value, str):  # 如果是字符串类型
                    values.append(f"'{escape_string(value)}'")  # 转义并加引号
                else:
                    values.append(f"{value}")  # 直接添加
            values_list.append(f"({', '.join(values)})")

        # 构建ON DUPLICATE KEY UPDATE部分（排除created_at字段）
        update_fields = [field for field in field_names if field not in ['created_at']]
        duplicate_str = ",".join([f"`{field}`=VALUES(`{field}`)" for field in update_fields])

        # 构建完整的INSERT语句
        insert_sql = (f"INSERT INTO `{table_name}`({fields_str}) VALUES {','.join(values_list)}"
                      f" ON DUPLICATE KEY UPDATE {duplicate_str};")

        try:
            self.cursor.execute(insert_sql)
            self.connect.commit()
        except Exception as e:
            self.connect.rollback()
            logger.error(f"执行 SQL 语句时发生错误: {e}")
            raise

    def _table_exists(self, table_name):
        """
        检查表是否存在
        :param table_name: 表名
        :return: bool
        """
        try:

            sql = f"SELECT 1 FROM `{table_name}` LIMIT 1;"  # noqa
            self.cursor.execute(sql)
            return True
        except Exception as e:
            logger.info(f"【{table_name}】不存在,为您重新创建: {e}")
            return False

    def _create_table(self, items, table_name, primary_key=None, uu_id=None, user=None):
        """
        根据数据自动创建表
        :param items: 数据列表
        :param table_name: 表名
        :param primary_key: 主键字段名
        user: 是否添加创建用户，更新用户
        :return:
        """
        if not items:
            return

        # 获取items中，字段中最长的一条数据，组成新的字段
        sample_item = get_long_values(items)
        columns = []
        keys = list(sample_item.keys())  # 获取所有字段名

        if primary_key:
            columns.append("`id` INT AUTO_INCREMENT UNIQUE")  # 添加自增ID字段，为唯一键
        else:
            columns.append("`id` INT AUTO_INCREMENT PRIMARY KEY")  # 添加自增ID字段,作为主键

        # 判断字段类型并添加主键字段
        for key in keys:
            # 根据值的类型推断字段类型
            value = sample_item[key]
            str_value = str(value) if value is not None else ""
            is_date = get_is_date(value)
            if is_date:
                if len(str_value) <= 10:  # 只有日期部分
                    column_type = "DATE"
                else:  # 包含时间部分
                    column_type = "DATETIME"
            elif ((isinstance(value, (int, float)) or
                   (isinstance(value, str) and value.replace('.', '').isdigit())) and len(str_value) < 10):
                # 长度不大于10，并且是数字
                # 数值类型使用 DOUBLE
                column_type = "DOUBLE"
            elif len(str_value) > 500:
                column_type = "TEXT"
            else:
                column_type = f"VARCHAR({min(max(len(str_value) * 2, 50), 1000)})"

            # 设置主键

            if key == primary_key:
                columns.append(f"`{key}` {column_type} PRIMARY KEY")
            else:
                columns.append(f"`{key}` {column_type}")

        # 添加UU_ID字段
        if uu_id:
            columns.append(f"`uu_id` VARCHAR(36) UNIQUE")  # UU_ID通常为36个字符

        # 添加创建时间和更新时间字段
        columns.append("`create_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        columns.append("`update_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")

        # 添加创建用户和更新用户字段
        if user:
            columns.append("`create_user` VARCHAR(50) DEFAULT NULL")
            columns.append("`update_user` VARCHAR(50) DEFAULT NULL")

        # 构建创建表的SQL语句
        create_sql = f"CREATE TABLE `{table_name}` ({', '.join(columns)});"  # noqa

        try:
            self.cursor.execute(create_sql)
            if user:
                # 创建触发器
                self._create_triggers(table_name)
            self.connect.commit()
            logger.info(f"表 `{table_name}` 创建成功")
        except Exception as e:
            logger.error(f"创建表 `{table_name}` 失败: {e}")
            raise

    def _check_and_update_table_structure(self, items, table_name):
        """
        检查表结构是否需要更新，并自动添加新字段
        """
        # 获取现有表结构
        existing_columns = self._get_existing_columns(table_name)

        # 获取新数据中的字段
        new_columns = set(items[0].keys())

        # 找到需要添加的新字段
        columns_to_add = new_columns - existing_columns

        # 如果有新字段需要添加，则执行ALTER TABLE操作
        if columns_to_add:
            alter_sql = self._build_alter_table_sql(table_name, columns_to_add, items)
            self.execute_sql(alter_sql)
            logger.info(f"表 {table_name} 已成功添加新字段: {list(columns_to_add)}")

    def _get_existing_columns(self, table_name):
        """获取现有表的列名"""
        sql = f"SHOW COLUMNS FROM `{table_name}`;"
        results = self.execute_sql(sql, fetch=True)
        return {result[0] for result in results}

    @staticmethod
    def _build_alter_table_sql(table_name, columns_to_add, items):
        """构建ALTER TABLE SQL语句"""
        alter_parts = []
        for column in columns_to_add:
            # 根据值推断字段类型
            value = next(item[column] for item in items if column in item)
            str_value = str(value) if value is not None else ""

            if len(str_value) > 1000:
                column_type = "TEXT"
            else:
                column_type = f"VARCHAR({min(max(len(str_value) * 2, 50), 1000)})"
            # 添加字段注释，包含添加时间
            comment = f"add_{get_date()}"
            comment_encoded = comment.encode('utf-8').decode('utf-8')
            alter_parts.append(f"ADD COLUMN `{column}` {column_type} COMMENT '{comment_encoded}'")

        alter_sql = f"ALTER TABLE `{table_name}` {' ,'.join(alter_parts)};"
        logger.info(alter_sql)

        return alter_sql

    def _create_triggers(self, table_name):
        # 为指定表创建自动设置用户信息的触发器，主要是记录哪个用户写入的数据

        # 创建INSERT/UPDATE触发器
        triggers = [
            (f"CREATE TRIGGER `before_insert_{table_name}` BEFORE INSERT ON `{table_name}` FOR EACH ROW "
             "BEGIN SET NEW.create_user = USER(); END;"),
            (f"CREATE TRIGGER `before_update_{table_name}` BEFORE UPDATE ON `{table_name}` FOR EACH ROW "
             "BEGIN SET NEW.update_user = USER(); END;")
        ]

        # 执行触发器创建语句
        for trigger_sql in triggers:
            try:
                self.cursor.execute(trigger_sql)
            except Exception as e:
                logger.warning(f"表 `{table_name}`创建触发器失败（可能由于权限问题）: {e}")

        self.connect.commit()
        logger.info(f"表 `{table_name}` 创建用户插入和更新触发器成功")

    def insert_delete_insert_data(self, items, db_table_name, delete_min_date, delete_max_date, shop_name,
                                  date_column_name='日期', uu_id=None, user=None):

        """
            先插入2条测试,如果插入成功,则先删除后入
            不需要指定key
        Args:
            items: 要插入的数据列表
            db_table_name: 目标表名
            delete_min_date: 删除数据的最小日期
            delete_max_date: 删除数据的最大日期
            shop_name: 店铺名称，用于过滤要删除的数据
            date_column_name: 日期字段名，默认为 "日期"
            uu_id: 是否为每条记录添加  UUID字段（默认不添加）
            user: 是否添加更新用户触发器

        Returns:
            bool: 操作是否成功
       """

        if not items:
            logger.warning("没有需要插入的数据")
            return False

        try:
            # 1. 测试插入前2条数据
            logger.info(f"开始测试插入2条数据到表 {db_table_name}")
            self.update_insert_date(items[:2], db_table_name, primary_key=None, uu_id=uu_id, user=user)
            logger.info(f"{db_table_name}测试插入成功")

            # 2. 构建删除SQL语句
            delete_sql = (f"DELETE FROM `{db_table_name}` "
                          f"WHERE `{date_column_name}` BETWEEN '{delete_min_date}' AND '{delete_max_date}' "
                          f"and `店铺名称`='{shop_name}';")

            # 3. 执行删除操作
            logger.info(f"开始删除指定日期范围内的数据")
            self.execute_sql(delete_sql)
            logger.info(f"删除成功，已删除【{shop_name}】 {delete_min_date} 到 {delete_max_date} 之间的数据")

            # 4. 批量插入所有数据
            logger.info(f"开始批量插入数据")
            self.update_insert_date(items, db_table_name, primary_key=None, uu_id=uu_id, user=user)
            logger.info(f"【{shop_name}】 {delete_min_date} 到 {delete_max_date} 批量插入完成")
            self.close()
            return True

        except Exception as e:
            self.close()
            logger.error(f"数据更新失败: {e}")
            raise

    def close(self):
        # 关闭游标和连接
        self.cursor.close()
        self.connect.close()


if __name__ == '__main__':
    db = DBManager()
