import pymysql
from pymysql.converters import escape_string
from extra.settings import *
from extra.logger_ import logger


class DatabaseManager:
    def __init__(self):
        db_params = dict(
            host=MYSQL_HOST,
            db=MYSQL_DBNAME,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            port=MYSQL_PORT,
        )
        self.connect = pymysql.connect(**db_params)
        self.cursor = self.connect.cursor()

    def upsert_data(self, items, table_name, primary_key=None):
        """
        新增或更新数据，如果表不存在则自动创建
        :param items: 要插入的数据列表，每个元素是一个字典
        :param table_name: 目标表名
        :param primary_key: 主键字段名，默认为数据中的第一个字段
        :return:
        """
        if not items:
            return

        # 检查表是否存在，如果不存在则创建
        if not self._table_exists(table_name):
            self._create_table(items, table_name, primary_key)

        v_list = []
        for j in items:  # 遍历每个数据字典
            k_str = ""  # 字段名字符串
            v_str = ""  # 值字符串
            for k, v in j.items():  # 遍历字典中的每个键值对
                k_str += f"`{k}`,"  # 构建字段名部分，用反引号包围
                if not v:  # 如果值为空
                    v_str += "NULL,"
                elif isinstance(v, str):  # 如果是字符串类型
                    v_str += f"'{escape_string(v)}',"  # 转义并加引号
                else:
                    v_str += f"{v},"  # 直接添加
            v_list.append(f"({v_str[0:-1]})")  # 去掉末尾逗号，用括号包围

        # 构建ON DUPLICATE KEY UPDATE部分（排除created_at字段）
        update_keys = [key for key in items[0].keys() if key not in ['created_at']]
        duplicate_str = ",".join([f"`{i}`=VALUES(`{i}`)" for i in update_keys])

        # 构建完整的INSERT语句
        insert_ignore_sql = f"INSERT INTO `{table_name}`({k_str[0:-1]}) VALUES {','.join(v_list)} ON DUPLICATE KEY UPDATE {duplicate_str};"

        self.cursor.execute(insert_ignore_sql)
        self.connect.commit()

    def _table_exists(self, table_name):
        """
        检查表是否存在
        :param table_name: 表名
        :return: bool
        """
        try:
            self.cursor.execute(f"SELECT 1 FROM `{table_name}` LIMIT 1;")
            return True
        except Exception:
            return False

    def _create_table(self, items, table_name, primary_key=None):
        """
        根据数据自动创建表
        :param items: 数据列表
        :param table_name: 表名
        :param primary_key: 主键字段名，默认为第一个字段
        :return:
        """
        if not items:
            return

        # 分析第一条数据的字段类型
        sample_item = items[0]
        columns = []
        keys = list(sample_item.keys()) # 获取所有字段名

        # 添加主键字段
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

        # 添加创建时间和更新时间字段
        columns.append("`create_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        columns.append("`update_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")

        # 构建创建表的SQL语句
        create_sql = f"CREATE TABLE `{table_name}` ({', '.join(columns)});"

        try:
            self.cursor.execute(create_sql)
            self.connect.commit()
            logger.info(f"表 `{table_name}` 创建成功")
        except Exception as e:
            logger.error(f"创建表 `{table_name}` 失败: {e}")
            raise

    def do_sql(self,sql):
        self.cursor.execute(sql)
        self.connect.commit()


    def select_cookies_shop(self, site: str ,shop_names: str):
        """
        查询语句
        :param :
        :return:
        """
        sql = f"select `店铺名称`,`cookie_str` from `cookie` where  `站点`='{site}' and `店铺名称` in {shop_names};"

        self.cursor.execute(sql)
        self.connect.commit()
        res = self.cursor.fetchall()
        return res

    def select_cookies_all(self, site: str ):
        """
        查询语句
        :param :
        :return:
        """
        sql = f"select `店铺名称`,`cookie_str` from `cookie` where  `站点`='{site}';"

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