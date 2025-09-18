import os

MYSQL_HOST = "223.5.242.173"
MYSQL_USER = "jishubu_baike"
MYSQL_PASSWORD = "baike@2024"
MYSQL_DBNAME = os.environ.get("MYSQL_DB") if os.environ.get("MYSQL_DB") else "baike_test"
MYSQL_PORT = 3306
LOGFILE = False if os.environ.get("LOGFILE", "1")=="0" else True
table_mapping = {
    "goods_data__goods_general_situation": {
        "cn_table_name": "pdd_数据中心_商品数据_商品概况",
        "en_table_name": "goods_data__goods_general_situation"
    },
    "goods_data__goods_detail": {
        "cn_table_name": "pdd_数据中心_商品数据_商品明细_商品明细效果",
        "en_table_name": "goods_data__goods_detail"
    },
    "flow_data__flow_board": {
        "cn_table_name": "pdd_数据中心_流量数据",
        "en_table_name": "flow_data__flow_board"
    }
    ,
    "service_data__after_sales_data": {
        "cn_table_name": "pdd_数据中心_服务数据_售后数据",
        "en_table_name": "service_data__after_sales_data"
    },
    "trade_data__data_overview": {
        "cn_table_name": "pdd_数据中心_交易数据_数据总览",
        "en_table_name": "trade_data__data_overview"
    },
    "goods_data__goods_general_situation_realtime": {
        "cn_table_name": "pdd_数据中心_商品数据_商品概况_实时",
        "en_table_name": "realtime_goods_data__goods_general_situation"
    }
}

accout_name = [
    "林内官方旗舰店:龙文章", "可丽蓝官方旗舰店:冯翎", "健美生旗舰店商央", "健美生专卖店商央", "Jamieson海外旗舰店商央",
    "悦康海外专卖店商央", "荷柏瑞官旗2店:文羽", "荷柏瑞PDD:一元", "vitacoco一元", "vitacoco_一元",
    "冷酸灵官方旗舰店:技术部", "冷酸灵个人护理旗舰店:技术部", "冷酸灵口腔护理官方旗舰店:技术部",
    "德国高端卫浴体验店一元元", "美的空调专卖店一元", "华凌康睿麦专卖店一元", "美的冷柜旗舰店一元", "小天鹅康趣一元",
    "小天鹅洗衣机一元", "惠购洗衣机专营店一元", "美的洗衣机旗舰店一元", "美的洗烘一元", "臻选大家电专营店一元",
    "容声康睿麦专卖店一元", "健美生专营店商央"
]

MAX_WAIT_TIME = 5
MIN_WAIT_TIME = 3