
# File: WanXiangTaiReport
import uuid

from WanXiangTaiApi.WanXiangTaiBase import WanXiangTaiBaseApi


class WanXiangTaiReportApi(WanXiangTaiBaseApi):
    """
    报表
    """
    def __init__(self, cookie):
        super().__init__(cookie)
        self.cookie = cookie

    def main_report__main_data_details(self):
        """
        主体报表》》主体数据明细
        :return:
        """
        data = {
            "excelName": f"主体报表_{self.get_date(0, '%Y%m%d')}_{uuid.uuid4().hex[:8]}",
            "pageSize": 20,
            "offset": 0,
            "havingList": [],
            "endTime": self.get_date(-1),
            "from": "pcBaseReport",
            "unifyType": "zhai",
            "effectEqual": 15,
            "startTime": self.get_date(-30),
            "splitType": "day",
            "subPromotionTypes": ["ITEM_PRIVATE_MINI", "SHOP", "USER_DEFINE_URL", "SHORT_VIDEO", "ITEM", "RSS_CONTENT"],
            "queryFieldIn": ["adPv", "click", "charge", "ctr", "ecpc", "alipayInshopAmt", "alipayInshopNum", "cvr",
                             "cartInshopNum", "itemColInshopNum", "shopColDirNum", "colNum", "itemColInshopCost"],
            "vsType": "week",
            "vsTime": self.get_date(-1),
            "searchValue": "",
            "searchKey": "itemIdOrName",
            "queryDomains": ["promotion", "date", "campaign"],
            "fieldType": "all",
            "rptType": "item_promotion",
            "parentAdcName": "report_frame_item_promotion",
            "byPage": False,
            "fromRealTime": False,
            "source": "async_dowdload",
            "csrfId": self.csrfId,
            "bizCode": "universalBP",
            "loginPointId": self.loginPointId}
        task_id = self.create_download_task(data)
        # print(task_id)
        return task_id

    def keyword_report__main_data_details(self):
        """
        关键词报表》》主体数据明细
        :return:
        """
        data = {"excelName": f"关键词报表_{self.get_date(0, '%Y%m%d')}_{uuid.uuid4().hex[:8]}",
                "_list": {"pageSize": 20,
                          "offset": 0,
                          "havingList": [],
                          "searchValue": "",
                          "searchKey": "strategyBidwordNameLike",
                          "queryDomains": ["word", "date", "campaign", "adgroup"],
                          "bizCodeIn": ["onebpSearch"]
                          },
                "pageSize_mx_list": 20,
                "offset": 0,
                "offset_mx_list": 0,
                "havingList": [],
                "havingList_mx_list": [],
                "endTime": self.get_date(-1),
                "from": "pcBaseReport",
                "unifyType": "zhai",
                "effectEqual": 15,
                "startTime": self.get_date(-30),
                "splitType": "day",
                "bizCodeIn": ["onebpSearch"],
                "_sum": {"bizCodeIn": ["onebpSearch", "onebpStarShop"],
                         "vsType": "week",
                         "vsTime": self.get_date(-1)
                         },
                "bizCodeIn_mx_sum": ["onebpSearch", "onebpStarShop"],
                "isKeyWordNotContainChase": "true",
                "queryFieldIn": ["adPv", "click", "charge", "ctr", "ecpc", "alipayInshopAmt", "alipayInshopNum", "cvr",
                                 "cartInshopNum", "itemColInshopNum", "shopColDirNum", "colNum", "itemColInshopCost",
                                 "avgRank"], "vsType_mx_sum": "week", "vsTime_mx_sum": "2025-04-20", "searchValue": "",
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
                "loginPointId": self.loginPointId}
        task_id = self.create_download_task(data)
        # print(task_id)
        return task_id

    def crowd_report__main_data_details(self,start_date,end_date):
        """
        "tb_tg_万相台无界_基础报表_人群报表_202504"
        """
        data = {"excelName": f"人群报表_{start_date}_{end_date}{uuid.uuid4().hex[:8]}",
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
                "queryFieldIn": ["adPv", "click", "charge", "ctr", "ecpc", "alipayInshopAmt", "alipayInshopNum", "cvr",
                                 "cartInshopNum", "itemColInshopNum", "shopColDirNum", "colNum", "itemColInshopCost"],
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
                "loginPointId":self.loginPointId}

        task_id = self.create_download_task(data)
        # print(task_id)
        return task_id

# a=WanXiangTaiReportApi(cookie="_tb_token_=b8f0d703-2e1c-4387-9dd8-3d2aea55b819; dnk=; t=61f6d9516106249f280ae435a10c9a79; lgc=; wk_cookie2=1de33e37072f0ef696f0385c1905c161; _tb_token_=313e8b0136b3; wk_unb=UoH%2B4NPsNoWZlw%3D%3D; cookie2=154930697d8a50696d572651f93a5a2b; _nk_=; cna=QpKMIIUcNlICASeqbVq05Ozi; xlly_s=1; uc1=cookie14=UoYajlesvxuitQ%3D%3D&cookie21=W5iHLLyFfoaZ; lid=%E6%9E%97%E5%86%85%E5%8E%A8%E7%94%B5%E6%97%97%E8%88%B0%E5%BA%97%3A%E4%B8%80%E5%85%83; unb=2212373938588; sgcookie=E100eK9lKaPAvPh32Rhx0Wrk22pCjCjkxB5bozkp8amFcgczA32rvWtf1NHfxUu2ojxtBs783DIwl9uxSO34BRayC0%2Bb7lIdr%2FyMhdwJdjXBG549bamGOo6ypc%2B71miUKwlv; cancelledSubSites=empty; csg=2f4422ce; sn=%E6%9E%97%E5%86%85%E5%8E%A8%E7%94%B5%E6%97%97%E8%88%B0%E5%BA%97%3A%E4%B8%80%E5%85%83; tfstk=gIft2V63QkqMejOus5wnnvAtOfUh7sQadG7SinxihMIdAMXMhRS0MsIcvPJbbCfAvGjhiOcclqLfxM1_WC9mMZsCojx1IncAM9_XohbMsENAAMjv3P-DcnIclO43Z7bN7IRXDuVuZ4UTIMIthITblvTkPyY6heqZTIRbqkDnGdPJgG69dUBfRyLDoAM1cfTBOH8SCVsXfpiByURXcisXOpT2knGjGEiBAH8XGnsXGydINpD90x-jMTJwuYLzsofdO6L9B3_LUYDz9KokJNtKGj92TdHG5HhjG6BvdSTMf8uH0CxNJFI4afR6Ht1MO1ZQGQ6PvspWw-4wCZBd0CfQlAt5IGAC1T3jGwd9cgCHpcEpV17CaB93NzQCTGbN9Z0bGejkAN56M7ay6Ct69e50YftAdt1MQIo_Dn5dR16A4uflwYHSq3LmCyUK3xJ68uEkuOSKzayMJ34h-xk2K8TpqyUK3xJ68eKu-3Dq3p25.")
# # a.main_report__main_data_details()
# a.get_download_url("10568864")
