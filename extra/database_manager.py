import re
import pymysql
import uuid

from pymysql.converters import escape_string
from extra.settings import *
from extra.logger_ import logger


# 添加mysql语言注释
# noinspection SqlDialectInspection,SqlNoDataSourceInspection
class DatabaseManager:
    def __init__(self, db_config=None):
        if db_config is None:
            db_params = DATABASE_CONFIGS.get('test')
        else:
            db_params = DATABASE_CONFIGS.get(db_config)

        self.connect = pymysql.connect(**db_params)
        self.cursor = self.connect.cursor()

    def upsert_data(self, items, table_name, primary_key=None, uu_id=None, user=None):
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

        # 分析第一条数据的字段类型
        sample_item = items[0]
        columns = []
        keys = list(sample_item.keys())  # 获取所有字段名,并添加id字段

        if primary_key:
            columns.append("`id` INT AUTO_INCREMENT UNIQUE")  # 添加自增ID字段，为唯一键
        else:
            columns.append("`id` INT AUTO_INCREMENT PRIMARY KEY")  # 添加自增ID字段,作为主键

        # 判断字段类型并添加主键字段
        for key in keys:
            # 根据值的类型推断字段类型
            value = sample_item[key]
            str_value = str(value) if value is not None else ""
            if len(str_value) > 1000:
                column_type = "TEXT"
            else:
                column_type = f"VARCHAR({min(max(len(str_value) * 2, 255), 1000)})"

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

    def _create_triggers(self, table_name):
        """
        为指定表创建自动设置用户信息的触发器
        :param table_name: 表名
        :return:
        """

        # 创建INSERT触发器
        insert_trigger_sql = f"""
        CREATE TRIGGER `before_insert_{table_name}`  
        BEFORE INSERT ON `{table_name}` 
        FOR EACH ROW 
        BEGIN
            SET NEW.create_user = USER();
        END;
        """

        # 创建UPDATE触发器

        update_trigger_sql = f"""
        CREATE TRIGGER `before_update_{table_name}`  
        BEFORE UPDATE ON `{table_name}` 
        FOR EACH ROW 
        BEGIN
            SET NEW.update_user = USER();
        END;
        """

        # 执行触发器创建语句
        try:
            self.cursor.execute(insert_trigger_sql)
            self.cursor.execute(update_trigger_sql)
            self.connect.commit()
            logger.info(f"表 `{table_name}` 创建用户插入和更新触发器成功")
        except Exception as e:
            logger.warning(f"表 `{table_name}`创建用户插入和更新触发器失败（可能由于权限问题）: {e}")
            self.connect.rollback()

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

        self.cursor.execute(sql)
        self.connect.commit()
        res = self.cursor.fetchall()
        return res

    def select_cookies_all(self, site: str):

        sql = f"select `店铺名称`,`cookie_str`,`cookie`  from `cookie` where  `站点`='{site}';"

        self.cursor.execute(sql)
        self.connect.commit()
        res = self.cursor.fetchall()
        return res

    def close(self):
        """
        关游标，关连接
        :return:
        """
        self.cursor.close()
        self.connect.close()


if __name__ == '__main__':
    db = DatabaseManager()
