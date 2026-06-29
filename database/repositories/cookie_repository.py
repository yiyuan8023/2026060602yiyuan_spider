from config import get_cookie_database_name
from database.utils import quote_identifier


def _cookie_table(table_name):
    """Cookie 读写固定走 Cookie 源库，不跟随业务 DBManager 的当前库。"""
    return f"{quote_identifier(get_cookie_database_name())}.{quote_identifier(table_name)}"


class CookieRepositoryMixin:
    """Cookie 查询仓储，统一处理店铺列表参数化，避免任务脚本拼 SQL。"""

    def select_cookies_shop(self, site: str, shop_names):
        if isinstance(shop_names, str):
            raise TypeError("shop_names 请传入 list/tuple/set，不再传 SQL 片段")

        shop_names = list(shop_names)
        if not shop_names:
            return []

        # 店铺名用参数占位符传入，避免把 IN 条件交给任务脚本字符串拼接。
        placeholders = ", ".join(["%s"] * len(shop_names))
        sql = (
            f"SELECT {quote_identifier('店铺名称')}, {quote_identifier('cookie_str')}, {quote_identifier('cookie')} "
            f"FROM {_cookie_table('cookie')} "
            f"WHERE {quote_identifier('站点')}=%s AND {quote_identifier('店铺名称')} IN ({placeholders});"
        )
        return self.execute_sql(sql, params=[site, *shop_names], fetch=True)

    def select_cookies_all(self, site: str):
        sql = (
            f"SELECT {quote_identifier('店铺名称')}, {quote_identifier('cookie_str')}, {quote_identifier('cookie')} "
            f"FROM {_cookie_table('cookie')} "
            f"WHERE {quote_identifier('站点')}=%s;"
        )
        return self.execute_sql(sql, params=[site], fetch=True)

    def select_cookie_check_rows(self, site: str | None = None, shop_names=None):
        conditions = []
        params = []
        if site:
            conditions.append(f"{quote_identifier('站点')}=%s")
            params.append(site)

        if shop_names:
            if isinstance(shop_names, str):
                raise TypeError("shop_names 请传入 list/tuple/set，不再传 SQL 片段")
            shop_names = list(shop_names)
            placeholders = ", ".join(["%s"] * len(shop_names))
            conditions.append(f"{quote_identifier('店铺名称')} IN ({placeholders})")
            params.extend(shop_names)

        where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = (
            f"SELECT {quote_identifier('店铺名称')}, {quote_identifier('站点')}, "
            f"{quote_identifier('cookie_str')}, {quote_identifier('cookie')} "
            f"FROM {_cookie_table('cookie')} "
            f"{where_sql} "
            f"ORDER BY {quote_identifier('站点')}, {quote_identifier('店铺名称')};"
        )
        return self.execute_sql(sql, params=params, fetch=True)

    def select_cookie(self, site: str, shop_name: str):
        sql = (
            f"SELECT {quote_identifier('店铺名称')}, {quote_identifier('cookie_str')}, {quote_identifier('cookie')} "
            f"FROM {_cookie_table('cookie')} "
            f"WHERE {quote_identifier('站点')}=%s AND {quote_identifier('店铺名称')}=%s "
            "LIMIT 1;"
        )
        rows = self.execute_sql(sql, params=[site, shop_name], fetch=True)
        return rows[0] if rows else None

    def upsert_cookie(
        self,
        site: str,
        shop_name: str,
        cookie_str: str,
        cookie=None,
        cookie_dict=None,
        account=None,
        yingdao_account=None,
        maintainer_email=None,
    ):
        """写入 Cookie 源表 get_cookie；读取仍由 cookie 视图统一合并。"""
        key = f"{site}|{shop_name}"
        fields = [
            "店铺名称",
            "账号",
            "站点",
            "影刀执行账号",
            "维护人邮箱",
            "cookie",
            "cookie_str",
            "cookie_dict",
            "key",
        ]
        values = [
            shop_name,
            account,
            site,
            yingdao_account,
            maintainer_email,
            cookie,
            cookie_str,
            cookie_dict,
            key,
        ]
        insert_fields = ", ".join(quote_identifier(field) for field in fields)
        placeholders = ", ".join(["%s"] * len(fields))
        update_fields = [field for field in fields if field != "key"]
        duplicate_sql = ", ".join(
            f"{quote_identifier(field)}=VALUES({quote_identifier(field)})"
            for field in update_fields
        )
        sql = (
            f"INSERT INTO {_cookie_table('get_cookie')} ({insert_fields}) "
            f"VALUES ({placeholders}) "
            f"ON DUPLICATE KEY UPDATE {duplicate_sql}, {quote_identifier('updatetime')}=CURRENT_TIMESTAMP;"
        )
        self.execute_sql(sql, params=values)
