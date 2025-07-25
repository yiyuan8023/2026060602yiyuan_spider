import pymysql
from pymysql.converters import escape_string
from settings import *


class DB():
    def __init__(self):
        adbparams = dict(
            host=MYSQL_HOST,
            db=MYSQL_DBNAME,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            port=MYSQL_PORT,
        )
        self.connect = pymysql.connect(**adbparams)
        self.cursor = self.connect.cursor()

    def do_insert(self,items,table_name):
        """
        新增语句
        :param: items:
        :return:
        """



        v_list = []
        for j in items:
            k_str = ""
            v_str = ""
            for k, v in j.items():
                k_str += "`{}`,".format(k)
                if not v:
                    v_str += "Null,"
                elif isinstance(v, str):
                    v_str += "'{}',".format(escape_string(v))
                else:
                    v_str += "{},".format(v)
            v_list.append(f"({v_str[0:-1]})")
        duplicate_str = ",".join(["`{}`=values(`{}`)".format(i, i) for i in items[0].keys()])
        insert_ignore_sql = """insert into `{}`({}) VALUES {} ON duplicate KEY UPDATE {};""".format(table_name,k_str[0:-1],",".join(v_list), duplicate_str)

        self.cursor.execute(insert_ignore_sql)
        self.connect.commit()

    def do_sql(self,sql):
        self.cursor.execute(sql)
        self.connect.commit()



    def do_select_cookies(self, site: str ):
        """
        查询语句
        :param :
        :return:
        """
        sql = f"select `店铺名称`,`cookie_str` from `xj_cookie` where  `站点`='{site}';"

        self.cursor.execute(sql)
        self.connect.commit()
        res = self.cursor.fetchall()
        return res
    def do_select_cookies_jar(self, site: str ):
        """
        查询语句
        :param :
        :return:
        """
        sql = f"select `店铺名称`,`cookie` from `xj_cookie` where  `站点`='{site}';"

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