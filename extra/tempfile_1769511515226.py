import requests
import json


class DingTalkSheetConnector:
    """
    一个简单的钉钉表格连接器。
    对应影刀文档中的「建立钉钉表格连接」指令。
    """

    # 钉钉API的基础地址
    _BASE_URL = "https://api.dingtalk.com"

    def __init__(self, app_key: str, app_secret: str, user_id: str, workbook_id: str):
        """
        初始化连接器。

        :param app_key: 企业内部应用的AppKey
        :param app_secret: 企业内部应用的AppSecret
        :param user_id: 操作表格的用户ID (UserId)
        :param workbook_id: 要操作的表格ID (WorkbookId)
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.user_id = user_id
        self.workbook_id = workbook_id
        self.access_token = None  # 保存获取到的访问令牌

    def get_access_token(self) -> str:
        """
        获取钉钉开放平台的访问令牌 (Access Token)。
        这是调用后续所有API的前提，对应影刀指令的内部操作。

        :return: 访问令牌字符串
        :raises Exception: 当获取令牌失败时抛出异常
        """
        url = f"{self._BASE_URL}/v1.0/oauth2/accessToken"
        headers = {"Content-Type": "application/json"}
        data = {"appKey": self.app_key, "appSecret": self.app_secret}

        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        if "accessToken" in result:
            self.access_token = result["accessToken"]
            print(f"✓ Access Token 获取成功: {self.access_token[:20]}...")
            return self.access_token
        else:
            error_msg = result.get("message", "未知错误")
            raise Exception(f"获取Access Token失败: {error_msg}")

    def create_connection(self):
        """
        创建并返回钉钉表格连接对象。
        此方法集成了令牌获取，并返回一个包含必要信息的连接对象，
        可供后续操作表格的指令使用。

        :return: 连接配置字典 (模拟影刀指令输出的‘钉钉对象’)
        """
        try:
            token = self.get_access_token()
            # 构建并返回连接对象
            connection = {
                "app_key": self.app_key,
                "user_id": self.user_id,
                "workbook_id": self.workbook_id,
                "access_token": token,  # 核心凭证
                "base_url": self._BASE_URL,
                "_connector_instance": self,  # 保留实例以供扩展
            }
            print("✓ 钉钉表格连接已成功建立")
            return connection
        except Exception as e:
            print(f"✗ 建立连接失败: {e}")
            return None


# ============ 如何使用 ============
# 1. 填入你从钉钉开放平台获取的实际参数
CONFIG = {
    "app_key": "ding64jr7pwm9xm8fmrw",  # 替换为你的AppKey
    "app_secret": "MHqrsMVwl2X66hvzUwdyg_5w0L8y2QLSQ23bBtUecvkvHU6cIgY6LKv3dzqE9EZz",  # 替换为你的AppSecret
    "user_id": "0225664713639811",  # 替换为你的用户ID
    "workbook_id": "a2QnV4jyPJkYJO4X",  # 替换为你的表格ID
}

# 2. 创建连接器实例并建立连接
dingtalk_connector = DingTalkSheetConnector(**CONFIG)
dingtalk_instance = dingtalk_connector.create_connection()

# 3. 检查连接是否成功
if dingtalk_instance:
    print(f"连接对象内容: {json.dumps(dingtalk_instance, indent=2, default=str)}")
    # 现在你可以使用 `dingtalk_instance` 中的 access_token 和 workbook_id
    # 去调用其他钉钉表格API，例如读取单元格、写入数据等。
