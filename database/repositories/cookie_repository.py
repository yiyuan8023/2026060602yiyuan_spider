from database.utils import quote_identifier


class CookieRepositoryMixin:
    def select_cookies_shop(self, site: str, shop_names):
        if isinstance(shop_names, str):
            raise TypeError("shop_names 请传入 list/tuple/set，不再传 SQL 片段")

        shop_names = list(shop_names)
        if not shop_names:
            return []

        placeholders = ", ".join(["%s"] * len(shop_names))
        sql = (
            f"SELECT {quote_identifier('店铺名称')}, {quote_identifier('cookie_str')}, {quote_identifier('cookie')} "
            f"FROM {quote_identifier('cookie')} "
            f"WHERE {quote_identifier('站点')}=%s AND {quote_identifier('店铺名称')} IN ({placeholders});"
        )
        return self.execute_sql(sql, params=[site, *shop_names], fetch=True)

    def select_cookies_all(self, site: str):
        sql = (
            f"SELECT {quote_identifier('店铺名称')}, {quote_identifier('cookie_str')}, {quote_identifier('cookie')} "
            f"FROM {quote_identifier('cookie')} "
            f"WHERE {quote_identifier('站点')}=%s;"
        )
        return self.execute_sql(sql, params=[site], fetch=True)
