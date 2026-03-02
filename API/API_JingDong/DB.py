import pymysql
from pymysql.converters import escape_string
from log_ import logger

from settings_pass import *


class DB:
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

    def do_insert(self, items, table_name):
        """
        新增语句
        :param cn_en_items:
        :return:
        """
        try:
            if isinstance(items, dict):
                k_str = ""
                v_str = ""
                u_str = ""
                for k, v in items.items():
                    k_str += "`{}`,".format(k)
                    # u_str += "`{}` = values(`{}`),".format(k,k)
                    if not v and v != 0:
                        v_str += "Null,"
                    elif isinstance(v, str):
                        v_str += "'{}',".format(escape_string(v))
                    else:
                        v_str += "{},".format(v)
                duplicate_str = ",".join(
                    ["`{}`=values(`{}`)".format(i, i) for i in items.keys()]
                )
                insert_sql = """insert into `{}`({}) VALUES({}) ON duplicate KEY UPDATE {};""".format(
                    table_name, k_str[0:-1], v_str[0:-1], duplicate_str
                )
                # print(insert_sql)
                self.cursor.execute(insert_sql)
                self.connect.commit()
            elif isinstance(items, list):
                # print(items)

                v_list = []
                for j in items:
                    k_str = ""
                    v_str = ""
                    for k, v in j.items():
                        k_str += "`{}`,".format(k)
                        # u_str += "`{}` = values(`{}`),".format(k,k)
                        if not v:
                            v_str += "Null,"
                        elif isinstance(v, str):
                            v_str += "'{}',".format(escape_string(v))
                        else:
                            v_str += "{},".format(v)
                    v_list.append(f"({v_str[0:-1]})")
                duplicate_str = ",".join(
                    ["`{}`=values(`{}`)".format(i, i) for i in items[0].keys()]
                )
                insert_sql = """insert into `{}`({}) VALUES {} ON duplicate KEY UPDATE {};""".format(
                    table_name, k_str[0:-1], ",".join(v_list), duplicate_str
                )
                # print(insert_sql)
                self.cursor.execute(insert_sql)
                self.connect.commit()
            return 1
        except Exception as e:
            logger.error(e)
            return 0

    def do_select(self, shop_name: str = None):
        """
        查询语句
        :param :
        :return:
        """
        if not shop_name:
            sql = "select `店铺名称`,`cookie_str`,`维护人邮箱`,`账号` from `bc_cookie` where  `站点`='生意参谋' and `维护人邮箱` like '%@bi-cheng%';"
        else:
            shop_name_list = [f"'{i}'" for i in shop_name.split(",")]
            sql = f"select `店铺名称`,`cookie_str`,`维护人邮箱`,`账号` from `bc_cookie` where  `站点`='生意参谋' and `维护人邮箱` like '%@bi-cheng%' and `店铺名称` in ({','.join(shop_name_list)});"
            # print(sql)
        self.cursor.execute(sql)
        self.connect.commit()
        res = self.cursor.fetchall()
        return res

    def do_select_stats(self, stats_date):
        sql = "select `shop_name`,`info`,`num`,`remarks` from `crawl_data_stats` where  `stats_date`='{}'and (`num`=0 or `remarks` like '%0%');".format(
            stats_date
        )
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
