# -*- coding: utf-8 -*-
# @Time : 2024/7/15 15:58
# @Author : Shao0000
# @Email : Michael_Shao0000@aliyun.com
# @File : email_.py
# @Project : ExtraTool
import re
import smtplib
import os
import sys
from email.mime.text import MIMEText
from email.header import Header
from email.mime.multipart import MIMEMultipart

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import get_smtp_config


# shuju_python@bi-cheng.cn 邮箱组
def send_email(
    title,
    message_content,
    receiver_email: list = ["shuju_python@bi-cheng.cn"],
    content_type="text",
):
    smtp_config = get_smtp_config()
    sender_email = smtp_config["sender"]
    # 创建邮件正文
    # message_content = '这是一封来自Python程序的测试邮件！'
    msg = MIMEMultipart()
    msg["Subject"] = Header(title, "utf-8")
    msg["From"] = sender_email
    msg["To"] = ", ".join(receiver_email)
    # 设置抄送人（Cc），注意逗号分隔的邮件地址字符串
    # msg["Cc"] = ", ".join(cc_emails)
    if content_type == "text":
        msg.attach(MIMEText(message_content.encode("utf-8"), "plain", "utf-8"))
    else:
        # HTML格式的内容，这里设置了红色加粗的文本
        html_content = f"""
        <html>
          <body>
            {message_content}
          </body>
        </html>
        """
        # 将HTML内容添加到MIMEText对象中，并设置subtype为html
        html_part = MIMEText(html_content, "html")
        # 将html_part附加到根消息
        msg.attach(html_part)
    try:
        server = smtplib.SMTP_SSL(smtp_config["host"], smtp_config["port"])
        server.login(sender_email, smtp_config["password"])
        server.sendmail(sender_email, receiver_email, msg.as_string())

        print("邮件发送成功！")
    except Exception as e:
        print(e.args)
    finally:
        if "server" in locals():
            server.quit()


def replace_with_pattern(match):
    i = match.group()
    return f'<span style="color:red; font-weight:bold;white-space: nowrap;">{i}</span>'


def str_html(ori_re, content):
    """
    传一个字符串，把里面的某些正则匹配到的内容加粗标红
    :param ori_re:
    :param content:
    :return:
    """
    result = re.sub(ori_re, replace_with_pattern, content)
    result = result.replace("\n", "<br>")
    return f"<p>{result}</p>"


if __name__ == "__main__":
    # send_email("你是pd高手吗", "你就是pd高手", 'junqianshang@bi-cheng.cn')
    a = "这是一个0210-1234-5678的手机号码"
    h = str_html("(\d{3,4})-(\d{3,4})-(\d{3,4})", a)
    send_email("title", h, "shuju_python@bi-cheng.cn", "html")
