# 🐍 复制以下全部代码，保存为 read_dingtalk_doc.py（或直接粘贴使用）
import requests
import pandas as pd
from io import BytesIO
from typing import Optional


def read_dingtalk_doc_excel(
    doc_id: str,
    app_key: str,
    app_secret: str,
    sheet_name: Optional[str] = None,
    dtype: Optional[dict] = None,
) -> pd.DataFrame:
    """
    ✅ 官方 API 封装：读取钉钉「云文档」中的 Excel 文件（.xlsx）内容
    🔗 对应接口：GET /v1.0/knowledge/docs/{docId}/content
    📚 文档地址：https://open.dingtalk.com/document/orgdev/get-doc-content

    ✅ 特性：
      - 自动获取 access_token（无需手动管理）
      - 直接返回 pandas DataFrame（支持中文列名、日期、数字自动识别）
      - 支持指定 sheet（默认第一页）
      - 支持自定义列类型（如将“型号”设为 str，避免转为 float）

    📌 参数：
      doc_id      → 钉钉云文档 ID（字符串，如 'd1234567890abcdef'）
      app_key     → 钉钉应用 AppKey
      app_secret  → 钉钉应用 AppSecret
      sheet_name  → Excel 工作表名（如 '买赠规则'），None=第一个 sheet
      dtype       → 列类型字典，如 {'型号': str, '最少下单台数': int}

    ?? 返回：
      pandas.DataFrame：已解析的 Excel 表格（索引从 0 开始，列名 = Excel 第一行）
    """
    # Step 1: 获取 access_token
    token_url = "https://oapi.dingtalk.com/gettoken"
    token_resp = requests.get(
        token_url, params={"appkey": app_key, "appsecret": app_secret}, timeout=10
    )
    token_resp.raise_for_status()
    token_data = token_resp.json()
    if "access_token" not in token_data:
        raise RuntimeError(f"❌ 获取 token 失败：{token_data}")
    access_token = token_data["access_token"]

    # Step 2: 调用文档内容接口
    url = f"https://oapi.dingtalk.com/v1.0/knowledge/docs/{doc_id}/content"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    # Step 3: 解析 Excel 二进制流
    excel_bytes = BytesIO(resp.content)
    print(excel_bytes)
    try:
        df = pd.read_excel(excel_bytes, sheet_name=sheet_name, dtype=dtype or {})
        # 清理列名：去除首尾空格，转为字符串（避免 float 列名）
        df.columns = [str(col).strip() for col in df.columns]
        return df
    except Exception as e:
        raise RuntimeError(f"❌ 解析 Excel 失败：{e}")


# ✅ 示例调用（取消注释并填入你的参数即可运行）
if __name__ == "__main__":
    # 🔑 替换为你自己的值（3 个必填项）
    DOC_ID = (
        "YQBnd5ExVEwxonQdtAyp1k1w8yeZqMmz"  # ← 云文档链接中的 doc_id（必须是 d 开头！）
    )
    DOC_ID = (
        "YQBnd5ExVEwxonQdtAyp1k1w8yeZqMmz"  # ← 云文档链接中的 doc_id（必须是 d 开头！）
    )

    APP_KEY = "ding64jr7pwm9xm8fmrw"  # ← 你的 AppKey
    APP_SECRET = "MHqrsMVwl2X66hvzUwdyg_5w0L8y2QLSQ23bBtUecvkvHU6cIgY6LKv3dzqE9EZz"  # ← 你的 AppSecret

    # 0225664713639811

    try:
        df = read_dingtalk_doc_excel(
            doc_id=DOC_ID,
            app_key=APP_KEY,
            app_secret=APP_SECRET,
            # sheet_name="买赠规则",     # 可选：指定工作表名
            # dtype={"型号": str, "最少下单台数": int}  # 可选：强制列类型
        )
        print(f"✅ 成功读取 Excel，共 {len(df)} 行，{len(df.columns)} 列")
        print("列名：", list(df.columns))
        print("\n前 3 行数据：")
        print(df.head(3))
    except Exception as e:
        print("💥 错误：", str(e))
