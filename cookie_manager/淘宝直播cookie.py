"""
开发说明：
- 作者：一元
- 创建时间：2026-06-06 13:28:51
- 最近修改：2026-06-10 21:05:00
- 文件用途：手动触发淘系直播中控台 Cookie 准备流程，优先复用已保存直播 Cookie，失效时用生意参谋 Cookie 派生并写回 get_cookie。
- 业务范围：适用于淘系直播中控台 Cookie 维护，当前默认处理林内官方旗舰店。
- 依赖入口：调用 API.API_TaoXi_ZhiBo.get_taoxi_zhibo_cookie_header，日志走 extra.logger_。
- 验收方式：修改后执行 py_compile；真实验证时运行本脚本并确认 get_cookie 中淘系_直播中控台 Cookie 可被直播采集任务复用。
- 注意事项：本脚本不输出真实 Cookie；自动刷新依赖生意参谋 Cookie JSON 可用。
"""

from API.API_TaoXi_ZhiBo import get_taoxi_zhibo_cookie_header
from extra.logger_ import logger


SHOP_NAME_LIST = ["林内官方旗舰店"]


if __name__ == "__main__":
    for shop_name in SHOP_NAME_LIST:
        get_taoxi_zhibo_cookie_header(shop_name)
        logger.info(f"{shop_name} 淘系直播 Cookie 准备完成")
