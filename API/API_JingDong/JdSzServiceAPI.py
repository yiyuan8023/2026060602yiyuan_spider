# -*- coding: utf-8 -*-
# @Time : 2024/9/18 16:19
# @Author : Shao0000
# @Email : Shao0000@aliyun.com
# @File : JdSzServiceAPI.py
# @Project : JDSZ
from urllib.parse import urlencode

import requests

from API_Jdsz_Base import JdSzAPI


class JdSzServiceAPI(JdSzAPI):
    """
    京东商智》》商品
    """

    def __init__(self, cookie=None, shop_name=None,account_name=None):
        # 初始化cookie和店铺名称
        super().__init__(cookie,shop_name,account_name)


    def fetch_service_analysis__after_sale_service(self,startDate,endDate,date):
        """
        服务分析》》服务分析》》售后服务单量&服务核心指标
        :return:
        """
        host = "https://sz.jd.com"
        api = "/sz/api/serviceAnalysis/getSummaryData.ajax"
        params = {
            "date": date,
            "endDate": endDate,
            "startDate": startDate
        }
        url = host + api + "?" + urlencode(params)
        headers = self.common_headers(api, host)
        res = requests.get(url=url, headers=headers)
        self.req_log(res)
        # print(res.json())
        return res.json()


# JdSzServiceAPI(
#     "__jdv=95931165|direct|-|none|-|1726268447304;__jdu=17262684473031596641934;areaId=15;ipLoc-djd=15-1213-0-0;shshshfpa=87e11837-ef2f-b1b6-d4d5-726d54bb1d57-1726354921;shshshfpx=87e11837-ef2f-b1b6-d4d5-726d54bb1d57-1726354921;PCSYCityID=CN_330000_330100_0;user-key=bd2234d8-871c-4342-a04b-a0af5faa5f37;3AB9D23F7A4B3CSS=jdd03FYUWX24ZIV4C3SHN34MJ736HKTBNKSZEMVRI44D2GES4F7AYZ7C6ENJWGKJLY646FF6OCC3WTL4TQXZ34ZDIFDCXKIAAAAMR67XNYWIAAAAACYPW7LV7PPIEGAX;_gia_d=source_map_4;3AB9D23F7A4B3C9B=FYUWX24ZIV4C3SHN34MJ736HKTBNKSZEMVRI44D2GES4F7AYZ7C6ENJWGKJLY646FF6OCC3WTL4TQXZ34ZDIFDCXKI;TrackID=source_map_4-VeCSpUONLWpU57r32Wy-1m0J0UETLCccCgaROnkQZn88h349JuHwpuZEma41Vh1CosMK4zU6RG3-d6ThWJnbggUmhKhdUuRub_JDp36ph50kfIe9jIH_3YJQ0LUokif;thor=CD29DD035C470B44B96F330154F60EED2C103825FC18E36D2A72DF3AA7C4D069F5F48026DDD5027F44A0E763C05C04773DC33DF22376481C46B02289AF2B294AA0DBE580239F60A55B0C38F37B94E3D15840C4276010A20F4848E3B651B54A66AFB5A32895859BB750D27B805E4A076F91CF4D437516FE73E890A41A1128BD233B319C99DA1D65850A8E21F3834E78CC;flash=3_bUfKrQlgSBU8Pc8asbDg2Og20m4nw09DODw8DvnpIAUl2x7IYqHOhf8xkD1iP0l8CsEMorr2igGyOE-REGA_LVmPXUNt-Kn_FtV4T7X3W6p0LKgK9wxh09eCzwfKjRHMVO6RGJTbvwsZa2bkeWKmwpQKXNFKJTZfQHQE2MyQyO3v2TAr58Qrq8tUgRXaLaqw;light_key=AASBKE7rOxgWQziEhC_QY6yaSzKV-ODwr7Yp_K8t-OIY0mTvT4t1ZQCtDDOgQyDMiNtQ4J5uEuVRnHWLfpB3W7Kpft59Eg;pinId=5ielbAPrAn16XSvstWe_upOTLmjz9-rFtX37H5_fCPs;pin=%E5%87%AF%E8%BF%AA%E4%BB%95%E6%97%97%E8%88%B0%E5%BA%97%E4%B8%80%E5%85%83;unick=x5iv1c85wjle9d;ceshi3.com=000;_tp=PA0O05611ewkh35ThCZAsOo4flYQqIDKRm%2FbgAr64D19Eftp%2F46HvUXpP4o9gI09s8vIaqreO6VE7N6K5pJprU6NSp4kZ6bUnZ5d23bMXII%3D;_pst=%E5%87%AF%E8%BF%AA%E4%BB%95%E6%97%97%E8%88%B0%E5%BA%97%E4%B8%80%E5%85%83;shshshfpb=BApXSUJH49PRAF7YnHWhfAmYcGxrvfayNBmR0Tg5p9xJ1Mkwu-4C2;__jda=251704139.17262684473031596641934.1726268447.1726354859.1726441251.3;__jdb=251704139.20.17262684473031596641934|3.1726441251;__jdc=251704139").fetch_service_analysis__after_sale_service()
