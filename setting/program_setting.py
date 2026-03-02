programs_to_run = [
    {
        "name": "淘宝联盟CPS订单明细",
        "command": [
            "python",
            "tb_tk_淘宝联盟_数据分析_cps订单明细_订单结算明细报表_202505.py",
        ],
        "cwd": r"C:\Users\admin\Desktop\yiyuan_spider\淘系_淘宝联盟",
        "timeout": 3600,
    },
    {
        "name": "淘宝联盟商品分析",
        "command": ["python", "tb_tk_淘宝联盟_商品分析_202504.py"],
        "cwd": r"C:\Users\admin\Desktop\yiyuan_spider\淘系_淘宝联盟",
        "timeout": 1800,
    },
    {
        "name": "我报名的商品",
        "command": ["python", "tb_tk_淘宝联盟_商品分析_202504.py"],
        "cwd": r"C:\Users\admin\Desktop\yiyuan_spider\淘系_淘宝联盟",
        "timeout": 1800,
    },
    # {
    #     'name': '数据清理脚本',
    #     'command': ['python', 'data_cleanup.py'],
    #     'cwd': r'C:\Users\admin\Desktop\yiyuan_spider\utils',
    #     'timeout': 600
    # }
]
