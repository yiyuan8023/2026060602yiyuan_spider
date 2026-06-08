import os
import pandas as pd
from bs4 import BeautifulSoup
import re

from database import DBManager
from extra.logger_ import logger


class HtmlCommentExtractor:
    def __init__(self, html_content):
        self.html_content = html_content
        self.comments_data = []

    def extract_html_comments(self):
        """
        从HTML文件中提取评论信息，包含主评论和回复评论
        """
        try:
            soup = BeautifulSoup(self.html_content, "html.parser")
            msg_box = soup.find("div", class_="msgBox")

            if not msg_box:
                print("未找到评论区域")
                return self.comments_data

            messages = msg_box.find_all("div", class_="msg")

            for message in messages:
                # 提取用户头像
                img_tag = message.find("div", class_="userHeadImg").find("img")
                img_src = img_tag.get("src") if img_tag else None

                # 提取主评论
                msg_body = message.find(class_="msgBody")
                if msg_body:
                    self._extract_comment_info(msg_body, img_src, "主评论")

                # 提取回复评论
                msg_body_reply = message.find("div", class_="msgBodyReply")
                if msg_body_reply:
                    author_replies = msg_body_reply.find_all(
                        "div", class_="msgBodyReplyList"
                    )
                    for author_reply in author_replies:
                        self._extract_comment_info(author_reply, img_src, "回复评论")

        except Exception as e:
            print(f"处理html时出错: {str(e)}")

        return self.comments_data

    def _extract_comment_info(self, info_tag, img_src, comment_type):
        """
        提取单条评论信息（主评论或回复评论）

        Args:
            info_tag: BeautifulSoup对象，包含评论的HTML元素
            img_src: 用户头像链接
            comment_type: 评论类型（'主评论' 或 '回复评论'）
        """
        # 初始化字段
        nickname = "未知"
        location = "未知"
        time = "未知"
        content = ""
        like_num = 0

        try:
            if comment_type == "主评论":
                # 主评论提取逻辑
                user_name = info_tag.find("p", class_="userName")
                if user_name:
                    # 提取昵称
                    if user_name.contents:
                        nickname = user_name.contents[0]

                    # 提取地区和时间
                    location_time_span = user_name.find("span")
                    if location_time_span:
                        location_time_text = location_time_span.get_text().strip()
                        location, time = self._extract_location_time(location_time_text)

                # 提取评论内容
                reply_body = info_tag.find("p", class_="replyBody")
                if reply_body and reply_body.contents:
                    content = reply_body.contents[0]

                # 提取赞数量
                like_num = self._extract_like_num(reply_body)

            else:  # 回复评论
                user_name = info_tag.find("p", class_="userName")
                if user_name:
                    # 提取昵称
                    em_tag = user_name.find("em", class_="replyIcon")
                    if em_tag:
                        nickname = em_tag.next

                    # 提取时间
                    time_span = user_name.find("span", class_="userInfo")
                    if time_span:
                        time = time_span.next
                        location, time = self._extract_location_time(time_span.next)

                        # 提取评论内容
                reply_body = info_tag.find("p", class_="autherBody")
                if reply_body and reply_body.contents:
                    content = reply_body.contents[0]

                # 提取赞数量
                like_num = self._extract_like_num(reply_body)

        except Exception as e:
            print(f"提取评论信息时出错: {str(e)}")

        # 创建评论记录
        comment_info = {
            "图像链接": img_src or "",
            "昵称": nickname,
            "地址": location,
            "时间": time,
            "内容": content,
            "赞数量": like_num,
            "等级": comment_type,
        }

        self.comments_data.append(comment_info)

    @staticmethod
    def _extract_like_num(reply_body):
        """
        提取赞数量
        """
        if not reply_body:
            return 0

        try:
            reply_like_num = reply_body.find("span", class_="reply_like_num")
            if reply_like_num:
                like_text = reply_like_num.get_text().strip()
                like_match = re.search(r"赞\s+(\d+)", like_text)
                if like_match:
                    return int(like_match.group(1))
        except Exception as e:
            print(f"提取赞数量时出错: {str(e)}")

        return 0

    @staticmethod
    def _extract_location_time(location_time_text):
        # 提取地区和时间

        location_match = re.search(
            r"(\S+?)\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", location_time_text
        )
        if location_match:
            location = location_match.group(1).strip()
            time = location_match.group(2).strip()
            return location, time

        return {}


if __name__ == "__main__":
    table_name = "gzh_article_comments_202508"
    sql = "select * from `gzh_html_files_202508` where id =1"  # noqa
    html_files_records = DBManager().execute_sql(sql, fetch=True)

    for html_files_record in html_files_records:
        file = html_files_record[2]
        extractor = HtmlCommentExtractor(html_files_record[3])
        items = extractor.extract_html_comments()

        for item in items:
            item.update({"file": file})
            item["key"] = f"{item['图像链接']}_{item['昵称']}_{item['时间']}"

        DBManager().update_insert_data(
            items, table_name, primary_key="key", uu_id=True, user=True
        )
        # logger.info(f"数据已入库")
        logger.info("-" * 100)

    logger.info(f"\n{'*' * 120}")
