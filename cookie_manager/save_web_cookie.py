from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import time
from typing import List, Dict, Optional
import pymysql
from datetime import datetime
import os


class WebCookieManager:
    """
    网页Cookie管理器 - 支持获取Chrome浏览器Cookie并保存到MySQL数据库
    """

    def __init__(self, db_config: Dict = None):
        """
        初始化Cookie管理器

        Args:
            db_config (Dict): MySQL数据库配置
        """
        # 默认数据库配置
        default_config = {
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "your_password",
            "database": "web_cookies",
            "charset": "utf8mb4",
        }

        self.db_config = db_config or default_config
        self.driver = None
        self._init_database()

    def _init_database(self):
        """初始化数据库表"""
        try:
            # 先连接到MySQL服务器（不指定数据库）
            temp_config = self.db_config.copy()
            database_name = temp_config.pop("database")

            connection = pymysql.connect(**temp_config)
            cursor = connection.cursor()

            # 创建数据库（如果不存在）
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            connection.commit()
            cursor.close()
            connection.close()

            # 连接到指定数据库并创建表
            connection = pymysql.connect(**self.db_config)
            cursor = connection.cursor()

            # 创建cookies表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cookies (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    website VARCHAR(500) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    value TEXT,
                    domain VARCHAR(255),
                    path VARCHAR(255),
                    expires BIGINT,
                    secure TINYINT(1),
                    httponly TINYINT(1),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_website (website),
                    INDEX idx_name (name)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # 创建websites表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS websites (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    url VARCHAR(500) UNIQUE NOT NULL,
                    title VARCHAR(500),
                    last_visited TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_url (url)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            connection.commit()
            cursor.close()
            connection.close()
            print("✅ 数据库初始化成功")

        except Exception as e:
            print(f"❌ 数据库初始化失败: {str(e)}")

    def connect_to_chrome(self, debug_port: int = 9222) -> bool:
        """
        连接到已打开的Chrome浏览器

        Args:
            debug_port (int): Chrome调试端口，默认9222

        Returns:
            bool: 是否连接成功
        """
        try:
            # 配置Chrome选项以连接到现有浏览器
            chrome_options = Options()
            chrome_options.add_experimental_option(
                "debuggerAddress", f"127.0.0.1:{debug_port}"
            )

            # 连接到Chrome浏览器
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ 成功连接到Chrome浏览器")
            return True

        except Exception as e:
            print(f"❌ 连接Chrome浏览器失败: {str(e)}")
            print("请确保Chrome浏览器已启动并启用远程调试:")
            print("   1. 关闭所有Chrome浏览器")
            print("   2. 以调试模式启动Chrome:")
            print("      Windows: chrome.exe --remote-debugging-port=9222")
            print(
                "      Mac: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222"
            )
            print("      Linux: google-chrome --remote-debugging-port=9222")
            return False

    def open_new_chrome(self, url: str = None) -> bool:
        """
        打开新的Chrome浏览器窗口

        Args:
            url (str, optional): 要打开的网址

        Returns:
            bool: 是否打开成功
        """
        try:
            chrome_options = Options()
            # 可以添加其他选项，如无头模式等
            # chrome_options.add_argument('--headless')  # 无头模式

            self.driver = webdriver.Chrome(options=chrome_options)

            if url:
                self.driver.get(url)
                print(f"✅ 已打开网页: {url}")
            else:
                print("✅ 已打开新的Chrome浏览器窗口")

            return True

        except Exception as e:
            print(f"❌ 打开Chrome浏览器失败: {str(e)}")
            return False

    def get_current_url(self) -> Optional[str]:
        """
        获取当前页面URL

        Returns:
            Optional[str]: 当前页面URL
        """
        if not self.driver:
            print("❌ 浏览器未连接")
            return None

        try:
            return self.driver.current_url
        except Exception as e:
            print(f"❌ 获取当前URL失败: {str(e)}")
            return None

    def get_current_title(self) -> Optional[str]:
        """
        获取当前页面标题

        Returns:
            Optional[str]: 当前页面标题
        """
        if not self.driver:
            print("❌ 浏览器未连接")
            return None

        try:
            return self.driver.title
        except Exception as e:
            print(f"❌ 获取页面标题失败: {str(e)}")
            return None

    def get_cookies(self, url: str = None) -> List[Dict]:
        """
        获取指定网页的Cookie

        Args:
            url (str, optional): 网页URL，如果为None则获取当前页面Cookie

        Returns:
            List[Dict]: Cookie列表
        """
        if not self.driver:
            print("❌ 浏览器未连接")
            return []

        try:
            # 如果指定了URL，则导航到该页面
            if url:
                print(f"正在访问: {url}")
                self.driver.get(url)
                # 等待页面加载
                time.sleep(2)

            # 获取Cookie
            cookies = self.driver.get_cookies()
            print(f"✅ 获取到 {len(cookies)} 个Cookie")
            return cookies

        except Exception as e:
            print(f"❌ 获取Cookie失败: {str(e)}")
            return []

    def save_cookies_to_db(
        self, cookies: List[Dict], website: str, website_title: str = None
    ) -> bool:
        """
        保存Cookie到MySQL数据库

        Args:
            cookies (List[Dict]): Cookie列表
            website (str): 网站URL
            website_title (str, optional): 网站标题

        Returns:
            bool: 是否保存成功
        """
        try:
            connection = pymysql.connect(**self.db_config)
            cursor = connection.cursor()

            # 保存网站信息
            cursor.execute(
                """
                INSERT INTO websites (url, title, last_visited)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                title = VALUES(title), 
                last_visited = VALUES(last_visited)
            """,
                (website, website_title, datetime.now()),
            )

            # 删除该网站的旧Cookie
            cursor.execute("DELETE FROM cookies WHERE website = %s", (website,))

            # 保存新的Cookie
            cookie_data = []
            for cookie in cookies:
                cookie_data.append(
                    (
                        website,
                        cookie.get("name"),
                        cookie.get("value"),
                        cookie.get("domain"),
                        cookie.get("path"),
                        cookie.get("expiry"),
                        int(cookie.get("secure", False)),
                        int(cookie.get("httpOnly", False)),
                    )
                )

            cursor.executemany(
                """
                INSERT INTO cookies 
                (website, name, value, domain, path, expires, secure, httponly)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
                cookie_data,
            )

            connection.commit()
            cursor.close()
            connection.close()

            print(f"✅ 成功保存 {len(cookies)} 个Cookie到数据库")
            return True

        except Exception as e:
            print(f"❌ 保存Cookie到数据库失败: {str(e)}")
            return False

    def load_cookies_from_db(self, website: str) -> List[Dict]:
        """
        从MySQL数据库加载Cookie

        Args:
            website (str): 网站URL

        Returns:
            List[Dict]: Cookie列表
        """
        try:
            connection = pymysql.connect(**self.db_config)
            cursor = connection.cursor(pymysql.cursors.DictCursor)

            cursor.execute("SELECT * FROM cookies WHERE website = %s", (website,))
            rows = cursor.fetchall()

            cookies = []
            for row in rows:
                cookie = {
                    "name": row["name"],
                    "value": row["value"],
                    "domain": row["domain"],
                    "path": row["path"],
                    "expiry": row["expires"] if row["expires"] else None,
                    "secure": bool(row["secure"]),
                    "httpOnly": bool(row["httponly"]),
                }
                cookies.append(cookie)

            cursor.close()
            connection.close()
            print(f"✅ 从数据库加载到 {len(cookies)} 个Cookie")
            return cookies

        except Exception as e:
            print(f"❌ 从数据库加载Cookie失败: {str(e)}")
            return []

    def list_websites(self, limit: int = 50) -> List[Dict]:
        """
        列出数据库中保存的所有网站

        Args:
            limit (int): 限制返回数量

        Returns:
            List[Dict]: 网站列表
        """
        try:
            connection = pymysql.connect(**self.db_config)
            cursor = connection.cursor(pymysql.cursors.DictCursor)

            cursor.execute(
                """
                SELECT url, title, last_visited 
                FROM websites 
                ORDER BY last_visited DESC 
                LIMIT %s
            """,
                (limit,),
            )
            websites = cursor.fetchall()

            cursor.close()
            connection.close()
            return websites

        except Exception as e:
            print(f"❌ 获取网站列表失败: {str(e)}")
            return []

    def search_cookies(self, keyword: str) -> List[Dict]:
        """
        搜索包含关键词的Cookie

        Args:
            keyword (str): 搜索关键词

        Returns:
            List[Dict]: 匹配的Cookie列表
        """
        try:
            connection = pymysql.connect(**self.db_config)
            cursor = connection.cursor(pymysql.cursors.DictCursor)

            cursor.execute(
                """
                SELECT * FROM cookies 
                WHERE name LIKE %s OR value LIKE %s OR website LIKE %s
                ORDER BY created_at DESC
            """,
                (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"),
            )
            cookies = cursor.fetchall()

            cursor.close()
            connection.close()
            print(f"✅ 搜索到 {len(cookies)} 个匹配的Cookie")
            return cookies

        except Exception as e:
            print(f"❌ 搜索Cookie失败: {str(e)}")
            return []

    def close(self):
        """关闭浏览器连接"""
        if self.driver:
            self.driver.quit()
            print("✅ 浏览器连接已关闭")


def main():
    """主函数 - 使用示例"""

    # MySQL数据库配置
    db_config = {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "your_password",  # 请修改为你的MySQL密码
        "database": "web_cookies",
        "charset": "utf8mb4",
    }

    # 创建Cookie管理器
    cookie_manager = WebCookieManager(db_config)

    try:
        # 方法1: 连接到已打开的Chrome浏览器
        print("正在连接到Chrome浏览器...")
        if cookie_manager.connect_to_chrome():
            print("✅ 连接成功")
        else:
            # 如果连接失败，打开新的浏览器窗口
            print("正在打开新的Chrome浏览器...")
            if not cookie_manager.open_new_chrome():
                return

        # 获取当前页面信息
        current_url = cookie_manager.get_current_url()
        current_title = cookie_manager.get_current_title()

        print(f"当前页面: {current_title}")
        print(f"当前URL: {current_url}")

        # 如果没有指定网址，使用当前页面
        target_url = input("请输入要获取Cookie的网址 (直接回车使用当前页面): ").strip()
        if not target_url:
            target_url = current_url

        if target_url:
            # 获取Cookie
            print(f"正在获取 {target_url} 的Cookie...")
            cookies = cookie_manager.get_cookies(target_url)

            if cookies:
                # 保存Cookie到数据库
                website_title = cookie_manager.get_current_title()
                if cookie_manager.save_cookies_to_db(
                    cookies, target_url, website_title
                ):
                    print("✅ Cookie保存成功")
                else:
                    print("❌ Cookie保存失败")
            else:
                print("❌ 未获取到Cookie")
        else:
            print("❌ 无法确定目标网址")

        # 显示已保存的网站列表
        print("\n已保存的网站:")
        websites = cookie_manager.list_websites(20)
        for i, website in enumerate(websites, 1):
            print(f"{i}. {website['title'] or website['url']}")
            print(f"   URL: {website['url']}")
            print(f"   最后访问: {website['last_visited']}")
            print()

    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序执行出错: {str(e)}")
    finally:
        # 关闭浏览器连接
        cookie_manager.close()


def quick_get_cookies(url: str = None, db_config: Dict = None):
    """
    快速获取Cookie的便捷函数

    Args:
        url (str, optional): 网址，如果为None则使用当前打开的页面
        db_config (Dict, optional): 数据库配置
    """
    cookie_manager = WebCookieManager(db_config)

    try:
        # 尝试连接到已打开的浏览器
        if not cookie_manager.connect_to_chrome():
            print("无法连接到Chrome浏览器，正在打开新的浏览器...")
            if not cookie_manager.open_new_chrome(url):
                return

        # 获取Cookie
        cookies = cookie_manager.get_cookies(url)

        if cookies:
            # 确定网站URL
            if url:
                website = url
            else:
                website = cookie_manager.get_current_url()
                if not website:
                    website = "unknown"

            # 保存到数据库
            website_title = cookie_manager.get_current_title()
            cookie_manager.save_cookies_to_db(cookies, website, website_title)

            # 显示Cookie信息
            print(f"\n获取到的Cookie ({len(cookies)} 个):")
            for cookie in cookies[:5]:  # 只显示前5个
                print(f"  {cookie['name']}: {cookie['value'][:50]}...")

            if len(cookies) > 5:
                print(f"  ... 还有 {len(cookies) - 5} 个Cookie")
        else:
            print("未获取到Cookie")

    finally:
        cookie_manager.close()


# 使用示例
if __name__ == "__main__":
    # 运行主程序
    main()

    # 或者使用快速函数
    # db_config = {
    #     'host': 'localhost',
    #     'port': 3306,
    #     'user': 'root',
    #     'password': 'your_password',
    #     'database': 'web_cookies',
    #     'charset': 'utf8mb4'
    # }
    # quick_get_cookies("https://www.example.com", db_config)
