import pymysql
from pymysql.converters import escape_string
from twisted.enterprise import adbapi

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

    def do_insert(self, cn_en_items):
        """
        新增语句
        :param cn_en_items:
        :return:
        """
        for i in cn_en_items:
            item = i["item"]
            if item:
                if isinstance(item, dict):
                    k_str = ""
                    v_str = ""
                    u_str = ""
                    for k, v in item.items():
                        k_str += "`{}`,".format(k)
                        # u_str += "`{}` = values(`{}`),".format(k,k)
                        if not v:
                            v_str += "Null," if i[
                                                    "table_name"] == "pdd_数据中心_商品数据_商品明细_商品明细效果" else "0,"
                        elif isinstance(v, str):
                            v_str += "'{}',".format(escape_string(v))
                        else:
                            v_str += "{},".format(v)
                    duplicate_str = ",".join(["`{}`=values(`{}`)".format(i, i) for i in item.keys()])
                    insert_ignore_sql = """insert into `{}`({}) VALUES({}) ON duplicate KEY UPDATE {};""".format(
                        i["table_name"], k_str[0:-1],
                        v_str[0:-1], duplicate_str)
                    self.cursor.execute(insert_ignore_sql)
                    self.connect.commit()
                elif isinstance(item, list):

                    v_list = []
                    for j in item:
                        k_str = ""
                        v_str = ""
                        for k, v in j.items():
                            k_str += "`{}`,".format(k)
                            # u_str += "`{}` = values(`{}`),".format(k,k)
                            if not v:
                                v_str += "Null," if i["table_name"] == "pdd_数据中心_商品数据_商品明细_商品明细效果" else "0,"
                            elif isinstance(v, str):
                                v_str += "'{}',".format(escape_string(v))
                            else:
                                v_str += "{},".format(v)
                        v_list.append(f"({v_str[0:-1]})")
                    duplicate_str = ",".join(["`{}`=values(`{}`)".format(i, i) for i in item[0].keys()])
                    insert_ignore_sql = """insert into `{}`({}) VALUES {} ON duplicate KEY UPDATE {};""".format(
                        i["table_name"],
                        k_str[0:-1],
                        ",".join(v_list), duplicate_str)

                    self.cursor.execute(insert_ignore_sql)
                    self.connect.commit()

    def do_select(self, shop_name: str = None):
        """
        查询语句
        :param :
        :return:
        """
        if not shop_name:
            sql = "select `店铺名称`,`cookie_str`,`维护人邮箱` from `bc`.`bc_cookie` where  `站点`='拼多多' and `维护人邮箱` like '%@%';"
        else:
            shop_name_list = [f"'{i}'" for i in shop_name.split(",")]
            sql = f"select `店铺名称`,`cookie_str`,`维护人邮箱` from `bc`.`bc_cookie` where  `站点`='拼多多' and `店铺名称` in ({','.join(shop_name_list)}) and `维护人邮箱` like '%@%';"
            print(sql)
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
