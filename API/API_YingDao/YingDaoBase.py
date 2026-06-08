from extra.downloader.core import Downloader
from extra.extra_reqlog import req_log
from extra.logger_ import logger
from config import UA


class YingDaoApi:
    # 检测cookie有没有失效
    def __init__(self, cookie=None):
        self.cookie = cookie
        self.ua = UA
        self.headers = {"user-agent": self.ua}

    def get_yd_question(self):
        """
        获取影刀社区问题
        """

        api = "https://api.yingdao.com/api/noauth/v1/sns/forum/question/query"
        params = {"page": "1", "size": "20", "tags": "问答", "sort": "createTime"}
        headers = {
            "Referer": "https://www.yingdao.com/",
            "User-Agent": self.ua,
        }

        res = Downloader(api, params=params, headers=headers).download_web()
        items = []
        if req_log(res):
            questions = res.json().get("data", [])
            for question in questions:
                item = {
                    "问题id": question.get("uuid"),
                    "标题": question.get("title"),
                    "内容": question.get("content"),
                    "提问时间": question.get("createTime"),
                    "更新时间": question.get("updateTime"),
                    "浏览人数": question.get("browseCount"),
                    "回答人数": question.get("answerCount"),
                    "点赞人数": question.get("likeCount"),
                    "是否解决": question.get("isSolved"),
                }
                # print(item)
                items.append(item)
        # print( items)
        return items


if __name__ == "__main__":
    yd = YingDaoApi().get_yd_question()
