import os
import pandas as pd
from bs4 import BeautifulSoup
import re
from datetime import datetime
from extra.database_manager import DatabaseManager

def extract_html_comments(html_path):
    """
    从HTML文件中提取评论信息，包含赞的数量、作者回复和作者回复的赞数量
    """
    comments_data = []

    try:
        # with open(html_path, 'r', encoding='utf-8') as file:  # 读取HTML文件
        #     html_content = file.read()

        soup = BeautifulSoup(html_path, 'html.parser')  # 使用BeautifulSoup解析HTML
        msg_boxes = soup.find_all('div', class_='msgBox')  # 找到所有评论容器

        if not msg_boxes:
            print(f"在 {html_path} 中未找到评论区域")
            return comments_data

        for msg_box in msg_boxes:
            messages = msg_box.find_all('div', class_='msg')  # 查找所有评论条目

            for message in messages:
                # 提取用户头像和昵称

                user_name = message.find('p', class_='userName')  # 提取昵称 地区 时间

                if not user_name:
                    continue

                img_tag = message.find('div', class_='userHeadImg').find('img')
                if img_tag:
                    src = img_tag.get('src')  # 使用 .get() 安全获取
                else:
                    src = ""  # 提取用户头像

                # 提取昵称、地区和时间（从userName标签中）
                nickname = user_name.contents[0]  # 获取昵称

                location_time_span = user_name.find('span')  # 从span标签中提取地区和时间

                location = "未知"
                time = "未知"
                if location_time_span:
                    location_time_text = location_time_span.get_text().strip()
                    # 使用正则表达式提取地区和时间
                    location_match = re.search(r'(\S+?)\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', location_time_text)

                    if location_match:
                        location = location_match.group(1).strip()  # 获取地区
                        time = location_match.group(2).strip()  # 获取时间



                # 提取评论内容
                reply_body = message.find('p', class_='replyBody')
                if reply_body:
                    content = reply_body.contents[0]
                else:
                    content = ""

                # 提取赞的数量
                reply_like_num = reply_body.find('span', class_='reply_like_num')
                like_num = 0
                if reply_like_num:
                    like_text = reply_like_num.get_text().strip()
                    like_match = re.search(r'赞\s+(\d+)', like_text)
                    if like_match:
                        like_num = int(like_match.group(1))

                # 创建用户评论记录
                comment_info = {
                    '文件路径': html_path,  # 新增文件路径字段
                    '图像链接': src,
                    '昵称': nickname,
                    '地址': location,
                    '时间': time,
                    '内容': content,
                    '赞数量': like_num,
                    '作者回复': '',
                    '作者回复时间': '',
                    '作者回复内容': '',
                    '作者回复赞数量': '',

                }
                comments_data.append(comment_info)

                # 提取作者回复
                msg_body_reply = message.find('div', class_='msgBodyReply')
                if msg_body_reply:
                    author_replies = msg_body_reply.find_all('div', class_='msgBodyReplyList')

                    for author_reply in author_replies:
                        author_user_name = author_reply.find('p', class_='userName')
                        if author_user_name:
                            author_nickname = author_user_name.get_text().strip()

                            # 检查是否为作者回复
                            if '作者' in author_nickname:
                                author_time_span = author_user_name.find('span', class_='userInfo')

                                # 作者回复时间
                                if author_time_span:
                                    author_time = author_time_span.get_text().strip()
                                else:
                                    author_time = "未知"

                                # 提取作者回复内容
                                author_content = author_reply.find('p', class_='autherBody')
                                if author_content:
                                    author_content_text = author_content.contents[0]
                                else:
                                    author_content_text = ""

                                # 提取作者回复的赞数量
                                author_like_num = ''
                                author_reply_like_num = author_content.find('span', class_='reply_like_num')
                                if author_reply_like_num:
                                    author_like_text = author_reply_like_num.get_text().strip()
                                    author_like_match = re.search(r'赞\s+(\d+)', author_like_text)
                                    if author_like_match:
                                        author_like_num = int(author_like_match.group(1))

                                        # 更新评论记录中的作者回复信息
                                comment_info['作者回复'] = '是'
                                comment_info['作者回复时间'] = author_time
                                comment_info['作者回复内容'] = author_content_text
                                comment_info['作者回复赞数量'] = author_like_num

    except Exception as e:
        print(f"处理文件 {html_path} 时出错: {str(e)}")

    return comments_data


def extract_all_html_comments():
    """
    提取文件夹下所有HTML文件的评论
    """
    all_comments = []
    sql = f"select * from `gzh_html_files_202508`" # noqa
    items = DatabaseManager().execute_sql(sql, fetch=True)

    # 遍历文件夹中的所有文件
    for item in items:
        comments = extract_html_comments(item[3])
        all_comments.extend(comments)

    return all_comments


def save_to_excel(comments_data, output_path):
    """
    将评论数据保存为Excel文件
    """
    if not comments_data:
        print("没有找到任何评论数据")
        return

    # 创建DataFrame
    df = pd.DataFrame(comments_data)

    # 确保列的顺序
    columns_order = [
        '文件路径', '图像链接', '昵称', '地址', '时间', '内容', '赞数量',
        '作者回复', '作者回复时间', '作者回复内容', '作者回复赞数量',
    ]
    df = df[columns_order]

    # 保存为Excel文件
    df.to_excel(output_path, index=False)
    print(f"数据已保存到: {output_path}")




if __name__ == "__main__":

    output_path = r"C:\Users\admin\Desktop\新建文件夹 (4)\文小叔说html_comments.xlsx"  # 设置输出Excel文件路径

    print("开始提取HTML评论...")
    comments_data = extract_all_html_comments()  # 提取所有HTML评论
    print(f"共找到 {len(comments_data)} 条评论")

    save_to_excel(comments_data, output_path)  # 保存为Excel
    print("处理完成!")
