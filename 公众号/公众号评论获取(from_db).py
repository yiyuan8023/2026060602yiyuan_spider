import os
import pandas as pd
from bs4 import BeautifulSoup
import re

from extra.database_manager import DatabaseManager
from extra.logger_ import logger


class HtmlCommentExtractor:
    def __init__(self, html_content):
        self.html_content = html_content
        self.src = None  # 提取用户头像链接
        self.location = None
        self.time = None
        self.content = None
        self.like_num = 0
        self.nickname = None
        self.level = None
        self.comments_data = []
        # self.comments_data = [{
        #     # '文件路径': html_path,  # 新增文件路径字段
        #     '图像链接': self.src,
        #     '昵称': self.nickname,
        #     '地址': self.location,
        #     '时间': self.time,
        #     '内容': self.content,
        #     '赞数量': self.like_num,
        #     '等级': None,
        # }]

    def extract_info(self, info_tag, level='主评论'):
        # 提取用户头像和昵称
        user_name = info_tag.find('p', class_='userName')  # 提取昵称 地区 时间
        if user_name:
            img_tag = info_tag.find('div', class_='userHeadImg').find('img')
            if img_tag:
                self.src = img_tag.get('src')  # 使用 .get() 安全获取

            # 提取昵称、地区和时间（从userName标签中）
            self.nickname = user_name.contents[0]  # 获取昵称
            location_time_span = user_name.find('span')  # 从span标签中提取地区和时间

            if location_time_span:
                location_time_text = location_time_span.get_text().strip()
                # 使用正则表达式提取地区和时间
                location_match = re.search(r'(\S+?)\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', location_time_text)

                if location_match:
                    self.location = location_match.group(1).strip()  # 获取地区
                    self.time = location_match.group(2).strip()  # 获取时间

            # 提取评论内容
            reply_body = info_tag.find('p', class_='replyBody')
            if reply_body:
                self.content = reply_body.contents[0]

            # 提取赞的数量
            reply_like_num = reply_body.find('span', class_='reply_like_num')

            if reply_like_num:
                like_text = reply_like_num.get_text().strip()
                like_match = re.search(r'赞\s+(\d+)', like_text)
                if like_match:
                    self.like_num = int(like_match.group(1))

            # 创建用户评论记录
            comment_info = {
                # '文件路径': html_path,  # 新增文件路径字段
                '图像链接': self.src,
                '昵称': self.nickname,
                '地址': self.location,
                '时间': self.time,
                '内容': self.content,
                '赞数量': self.like_num,
                '等级': level,
            }
            self.comments_data.append(comment_info)
            return self.comments_data

    def extract_html_comments(self):
        """
        从HTML文件中提取评论信息，包含赞的数量、作者回复和作者回复的赞数量
        """
        try:
            soup = BeautifulSoup(self.html_content, 'html.parser')  # 使用BeautifulSoup解析HTML
            msg_boxes = soup.find_all('div', class_='msgBox')  # 找到所有评论容器

            if not msg_boxes:
                print(f"在 {self.html_content} 中未找到评论区域")
                # return None

            for msg_box in msg_boxes:
                messages = msg_box.find_all('div', class_='msg')  # 查找所有评论条目
                user_name = messages.find('p', class_='userName')  # 提取昵称 地区 时间
                if user_name:
                    img_tag = messages.find('div', class_='userHeadImg').find('img')
                    if img_tag:
                        self.src = img_tag.get('src')  # 使用 .get() 安全获取

                for message in messages:
                    # self.extract_info(message)

                    # 提取作者回复
                    msg_body_reply = message.find('div', class_='msgBodyReply')
                    if msg_body_reply:
                        author_replies = msg_body_reply.find_all('div', class_='msgBodyReplyList')
                        print(author_replies)

                        for author_reply in author_replies:
                            self.extract_info(author_reply, '回复评论')
            #
            #         author_user_name = author_reply.find('p', class_='userName')
            #         if author_user_name:
            #             author_nickname = author_user_name.get_text().strip()
            #
            #             # 检查是否为作者回复
            #             if '作者' in author_nickname:
            #                 author_time_span = author_user_name.find('span', class_='userInfo')
            #
            #                 # 作者回复时间
            #                 if author_time_span:
            #                     author_time = author_time_span.get_text().strip()
            #                 else:
            #                     author_time = "未知"
            #
            #                 # 提取作者回复内容
            #                 author_content = author_reply.find('p', class_='autherBody')
            #                 if author_content:
            #                     author_content_text = author_content.contents[0]
            #                 else:
            #                     author_content_text = ""
            #
            #                 # 提取作者回复的赞数量
            #                 author_like_num = ''
            #                 author_reply_like_num = author_content.find('span', class_='reply_like_num')
            #                 if author_reply_like_num:
            #                     author_like_text = author_reply_like_num.get_text().strip()
            #                     author_like_match = re.search(r'赞\s+(\d+)', author_like_text)
            #                     if author_like_match:
            #                         author_like_num = int(author_like_match.group(1))
            #
            #                         # 更新评论记录中的作者回复信息
            #                 comment_info['作者回复'] = '是'
            #                 comment_info['作者回复时间'] = author_time
            #                 comment_info['作者回复内容'] = author_content_text
            #                 comment_info['作者回复赞数量'] = author_like_num

        except Exception as e:
            print(f"处理html时出错: {str(e)}")

        return self.comments_data


if __name__ == "__main__":
    table_name = 'gzh_article_comments_202508'
    sql = f"select * from `gzh_html_files_202508`"  # noqa
    html_files_records = DatabaseManager().execute_sql(sql, fetch=True)
    print(html_files_records)

    # 遍历文件夹中的所有文件
    for html_files_record in html_files_records:
        file = html_files_record[2]
        ojb = HtmlCommentExtractor(html_files_record[3])
        items = ojb.extract_html_comments()
        for item in items:
            item.update({
                "file": file,
            })
            item["key"] = f"{item['昵称']}_{item['时间']}"

        # print(items)
        # print(items[0].keys())
        DatabaseManager().upsert_data(items, table_name, primary_key='key', uu_id=True, user=True)
        logger.info(f"数据已入库")
        logger.info("-" * 100)
    logger.info(f"\n{'*' * 120}")

    # output_path = r"D:\1921681859\AA\文小叔说html_comments.xlsx"  # 设置输出Excel文件路径
    #
    # print("开始提取HTML评论...")
    # comments_data = extract_all_html_comments()  # 提取所有HTML评论
    # print(f"共找到 {len(comments_data)} 条评论")
    #
    # save_to_excel(comments_data, output_path)  # 保存为Excel
    # print("处理完成!")
