import uuid
from API.API_TaoXi_WanXiangTai.WxtBase import WxtBaseApi


class WxtReportApi(WxtBaseApi):
    def __init__(self, cookie):
        super().__init__(cookie)
        self.cookie = cookie

    def wxt_baby_report(self, start_date, end_date):
        """
        tb_tg_万相台无界_基础报表_宝贝主体_202504
        """
        data = {
            "excelName": f"主体报表_{start_date}_{end_date}_{uuid.uuid4().hex[:8]}",
            "pageSize": 20,
            "offset": 0,
            "havingList": [],
            "endTime": end_date,
            "from": "pcBaseReport",
            "unifyType": "zhai",  # NOQA
            "effectEqual": 15,
            "startTime": start_date,
            "splitType": "day",
            "subPromotionTypes": [
                "ITEM_PRIVATE_MINI",
                "SHOP",
                "USER_DEFINE_URL",
                "SHORT_VIDEO",
                "ITEM",
                "RSS_CONTENT",
            ],
            "queryFieldIn": [
                "adPv",
                "click",
                "charge",
                "ctr",
                "ecpc",
                "alipayInshopAmt",
                "alipayInshopNum",
                "cvr",
                # NOQA
                "cartInshopNum",
                "itemColInshopNum",
                "shopColDirNum",
                "colNum",
                "itemColInshopCost",
            ],
            # NOQA
            "vsType": "week",
            "vsTime": end_date,
            "searchValue": "",
            "searchKey": "itemIdOrName",
            "queryDomains": ["promotion", "date", "campaign"],
            "fieldType": "all",
            "rptType": "item_promotion",
            "parentAdcName": "report_frame_item_promotion",
            "byPage": False,
            "fromRealTime": False,
            "source": "async_dowdload",  # NOQA
            "csrfId": self.csrfId,
            "bizCode": "universalBP",
            "loginPointId": self.loginPointId,
        }
        task_id = self.create_download_task(data)
        # print(task_id)
        return task_id

    def wxt_keyword_report(self, start_date, end_date):
        """
        tb_tg_万相台无界_基础报表_关键词_202504
        """
        data = {
            "excelName": f"关键词报表_{start_date}_{end_date}_{uuid.uuid4().hex[:8]}",
            "_list": {
                "pageSize": 20,
                "offset": 0,
                "havingList": [],
                "searchValue": "",
                "searchKey": "strategyBidwordNameLike",
                "queryDomains": ["word", "date", "campaign", "adgroup"],
                "bizCodeIn": ["onebpSearch"],
            },
            "pageSize_mx_list": 20,
            "offset": 0,
            "offset_mx_list": 0,
            "havingList": [],
            "havingList_mx_list": [],
            "endTime": end_date,
            "from": "pcBaseReport",
            "unifyType": "zhai",
            "effectEqual": 15,
            "startTime": start_date,
            "splitType": "day",
            "bizCodeIn": ["onebpSearch"],
            "_sum": {
                "bizCodeIn": ["onebpSearch", "onebpStarShop"],
                "vsType": "week",
                "vsTime": end_date,
            },
            "bizCodeIn_mx_sum": ["onebpSearch", "onebpStarShop"],
            "isKeyWordNotContainChase": "true",
            "queryFieldIn": [
                "adPv",
                "click",
                "charge",
                "ctr",
                "ecpc",
                "alipayInshopAmt",
                "alipayInshopNum",
                "cvr",
                "cartInshopNum",
                "itemColInshopNum",
                "shopColDirNum",
                "colNum",
                "itemColInshopCost",
                "avgRank",
            ],
            "vsType_mx_sum": "week",
            "vsTime_mx_sum": "2025-04-20",
            "searchValue": "",
            "searchValue_mx_list": "",
            "searchKey_mx_list": "strategyBidwordNameLike",
            "queryDomains": ["word", "date", "campaign", "adgroup"],
            "queryDomains_mx_list": ["word", "date", "campaign", "adgroup"],
            "bizCodeIn_mx_list": ["onebpSearch"],
            "pageSize": 20,
            "searchKey": "strategyBidwordNameLike",
            "fieldType": "all",
            "rptType": "bidword",
            "parentAdcName": "report_frame_bidword",
            "byPage": False,
            "fromRealTime": False,
            "source": "async_dowdload",
            "csrfId": self.csrfId,
            "bizCode": "universalBP",
            "loginPointId": self.loginPointId,
        }
        task_id = self.create_download_task(data)
        # print(task_id)
        return task_id

    def wxt_crowd_report(self, start_date, end_date):
        # tb_tg_万相台无界_基础报表_人群报表_202504

        data = {
            "excelName": f"人群报表_{start_date}_{end_date}_{uuid.uuid4().hex[:8]}",
            "pageSize": 20,
            "offset": 0,
            "havingList": [],
            "endTime": end_date,
            "from": "pcBaseReport",
            "unifyType": "zhai",
            "effectEqual": 15,
            "startTime": start_date,
            "splitType": "day",
            "filterAppendSubwayChannel": True,
            "filterNullCrowdSubwayTag": True,
            "queryFieldIn": [
                "adPv",
                "click",
                "charge",
                "ctr",
                "ecpc",
                "alipayInshopAmt",
                "alipayInshopNum",
                "cvr",
                "cartInshopNum",
                "itemColInshopNum",
                "shopColDirNum",
                "colNum",
                "itemColInshopCost",
            ],
            "vsType": "week",
            "vsTime": end_date,
            "searchValue": "",
            "searchKey": "strategyTargetTitleLike",
            "queryDomains": ["crowd", "promotion", "date", "campaign", "adgroup"],
            "fieldType": "all",
            "rptType": "crowd",
            "parentAdcName": "report_frame_crowd",
            "byPage": False,
            "fromRealTime": False,
            "source": "async_dowdload",
            "csrfId": self.csrfId,
            "bizCode": "universalBP",
            "loginPointId": self.loginPointId,
        }

        task_id = self.create_download_task(data)
        # print(task_id)
        return task_id

    def wxt_all_scene_report(self, start_date, end_date):
        """
        "tb_tg_万相台无界_基础报表_货品全站推_202504"
        """
        data = {
            "excelName": f"货品全站推报表_{start_date}_{end_date}_{uuid.uuid4().hex[:8]}",
            "queryFieldIn": [
                "charge",
                "adPv",
                "click",
                "itemColInshopNum",
                "cartInshopNum",
                "alipayInshopNum",
                "alipayInshopAmt",
                "alipayDirNum",
                "alipayDirAmt",
                "colCartCost",
                "ecpc",
                "ctr",
                "roi",
                "cvr",
            ],
            "pageSize": 20,
            "offset": 0,
            "havingList": [],
            "endTime": end_date,
            # "daterangeActivityId": 20251215,
            "activityType": "customActivity",
            "effectEqual": 15,
            "startTime": start_date,
            "splitType": "day",
            "unifyType": "last_click_by_effect_time",
            "itemSelectedMode": "all",
            "dataFlowId": "10786",
            "vsType": "week",
            "vsTime": end_date,
            "searchValue": "",
            "searchKey": "strategyCampaignIdOrName",
            "queryDomains": ["promotion", "date"],
            "bizCode": "onebpSite",
            "fieldType": "all",
            "rptType": "site",
            "parentAdcName": "report_frame_site",
            "byPage": False,
            "fromRealTime": False,
            "source": "async_dowdload",
            "csrfId": self.csrfId,
            "loginPointId": self.loginPointId,
        }

        task_id = self.create_download_task(data)
        # print(task_id)
        return task_id
