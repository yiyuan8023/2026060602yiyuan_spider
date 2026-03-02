import smtplib
from email.mime.text import MIMEText
from email.header import Header

from email.mime.multipart import MIMEMultipart

from extra.logger_ import logger


@logger.catch
def send_email(
    title,
    message_content,
    receiver_email: list = ["shuju_python@bi-cheng.cn"],
    content_type="text",
):
    # 设置发件人和收件人的邮箱地址
    sender_email = "sjbi@bi-cheng.cn"
    # receiver_email = 'junqianshang@bi-cheng.cn'
    # 邮箱服务器及端口，这里以QQ邮箱为例
    smtp_server = "smtp.qiye.aliyun.com"
    smtp_port = 465  # 对于大多数SMTP服务器，使用STARTTLS时默认为587
    # 邮箱授权码（而不是密码）
    password = "tZtHOQL5AEw8cGXY"

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
        # 连接SMTP服务器并启动安全传输模式
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        # server.starttls()  # 启用TLS或SSL加密

        # 登录SMTP服务器
        server.login(sender_email, password)

        # 发送邮件
        server.sendmail(sender_email, receiver_email, msg.as_string())

        logger.info("邮件发送成功！")
    except Exception as e:
        logger.error(e)

    finally:
        # 关闭SMTP连接
        server.quit()
