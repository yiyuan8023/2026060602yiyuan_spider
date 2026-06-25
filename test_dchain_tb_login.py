"""测试DChain淘宝登录"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from API_login.API_TaoXi_login.API_TaoXi_DC_TB_login import prepare_dchain_tb_cookie

result = prepare_dchain_tb_cookie(
    shop_name="林内供应商:BI_测试",
    login_id="林内供应商:BI",
    password="18668011375yi",
    site="DChain_TB",
    save_local=False,
)

print("=" * 60)
print(f"状态: {result.get('status')}")
print(f"消息: {result.get('message', '无')}")
print(f"Cookie数量: {result.get('cookie_count', 0)}")
print("=" * 60)
