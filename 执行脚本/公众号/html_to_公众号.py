# batch_wechat_converter.py
import os
from pathlib import Path
from html.parser import HTMLParser


class WeChatHTMLConverter(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []
        self.lists = []
        self.list_counters = []
        self.in_pre = False
        self.in_table = False
        self.table_rows = []
        self.current_row = []
        self.link_href = ""
        self.in_link = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            level = int(tag[1])
            # 微信公众号推荐的标题样式
            if level == 1:
                self.result.append(
                    '<p style="font-size:22px;font-weight:bold;color:#333;margin:20px 0 10px 0;text-align:center;">'
                )
            elif level == 2:
                self.result.append(
                    '<p style="font-size:20px;font-weight:bold;color:#333;margin:18px 0 8px 0;border-left:4px solid #576b95;padding-left:10px;">'
                )
            else:
                self.result.append(
                    '<p style="font-size:18px;font-weight:bold;color:#333;margin:15px 0 5px 0;">'
                )

        elif tag == "p":
            self.result.append(
                '<p style="font-size:16px;color:#333;margin:10px 0;line-height:1.75;">'
            )

        elif tag == "br":
            self.result.append("<br>")

        elif tag in ["strong", "b"]:
            self.result.append('<strong style="color:#333;">')

        elif tag in ["em", "i"]:
            self.result.append('<em style="color:#333;">')

        elif tag in ["del", "s"]:
            self.result.append('<del style="color:#999;">')

        elif tag == "code" and not self.in_pre:
            self.result.append(
                '<code style="background-color:#f6f8fa;color:#24292e;font-family:SFMono-Regular,Consolas,Liberation Mono,Menlo,monospace;font-size:14px;padding:2px 4px;border-radius:3px;">'
            )

        elif tag == "pre":
            self.in_pre = True
            self.result.append(
                '<pre style="background-color:#f6f8fa;color:#24292e;font-family:SFMono-Regular,Consolas,Liberation Mono,Menlo,monospace;font-size:14px;padding:12px;border-radius:6px;overflow:auto;margin:15px 0;line-height:1.4;">'
            )

        elif tag == "a":
            self.in_link = True
            self.link_href = attrs_dict.get("href", "")
            self.result.append(
                f'<a href="{self.link_href}" style="color:#576b95;text-decoration:none;border-bottom:1px solid #576b95;">'
            )

        elif tag == "img":
            src = attrs_dict.get("src", "")
            alt = attrs_dict.get("alt", "")
            self.result.append(
                f'<p style="text-align:center;margin:15px 0;"><img src="{src}" alt="{alt}" style="max-width:100%;height:auto;border-radius:6px;box-shadow:0 2px 12px 0 rgba(0,0,0,0.1);"></p>'
            )

        elif tag == "blockquote":
            self.result.append(
                '<blockquote style="border-left:4px solid #576b95;margin:15px 0;padding:10px 20px;background-color:#fafbfc;color:#666;font-style:italic;">'
            )

        elif tag in ["ul", "ol"]:
            self.lists.append(tag)
            self.list_counters.append(0 if tag == "ul" else 1)
            self.result.append('<div style="margin:10px 0;">')

        elif tag == "li":
            if self.lists:
                list_type = self.lists[-1]
                if list_type == "ul":
                    self.result.append(
                        '<p style="margin:8px 0;padding-left:20px;position:relative;"><span style="position:absolute;left:0;top:0;">•</span>'
                    )
                else:
                    counter = self.list_counters[-1]
                    self.result.append(
                        f'<p style="margin:8px 0;padding-left:25px;position:relative;"><span style="position:absolute;left:0;top:0;">{counter}.</span>'
                    )
                    self.list_counters[-1] += 1

        elif tag == "hr":
            self.result.append(
                '<div style="text-align:center;margin:25px 0;"><hr style="border:0;height:1px;background-color:#e1e4e8;width:80%;margin:0 auto;"></div>'
            )

    def handle_endtag(self, tag):
        if tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            self.result.append("</p>")
        elif tag == "p":
            self.result.append("</p>")
        elif tag in ["strong", "b"]:
            self.result.append("</strong>")
        elif tag in ["em", "i"]:
            self.result.append("</em>")
        elif tag in ["del", "s"]:
            self.result.append("</del>")
        elif tag == "code" and not self.in_pre:
            self.result.append("</code>")
        elif tag == "pre":
            self.in_pre = False
            self.result.append("</pre>")
        elif tag == "a":
            self.result.append("</a>")
            self.in_link = False
            self.link_href = ""
        elif tag == "blockquote":
            self.result.append("</blockquote>")
        elif tag in ["ul", "ol"]:
            if self.lists:
                self.lists.pop()
                self.list_counters.pop()
            self.result.append("</div>")
        elif tag == "li":
            self.result.append("</p>")

    def handle_data(self, data):
        if not data.strip() and not self.in_pre:
            return

        # 转义HTML特殊字符
        if not self.in_pre:
            data = data.replace("&", "&amp;")
            data = data.replace("<", "&lt;")
            data = data.replace(">", "&gt;")

        self.result.append(data)

    def get_wechat_html(self):
        content = "".join(self.result)
        wechat_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="background-color:#fff;padding:20px;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji;">
<div style="max-width:700px;margin:0 auto;background-color:#fff;">
{content}
</div>
</body>
</html>"""
        return wechat_html


def convert_html_to_wechat_format(html_content):
    """
    将HTML内容转换为适合微信公众号的格式
    """
    converter = WeChatHTMLConverter()
    converter.feed(html_content)
    return converter.get_wechat_html()


def batch_convert_html_files(source_folder, target_folder):
    """
    批量将HTML文件转换为微信公众号格式

    Args:
        source_folder (str): 源文件夹路径
        target_folder (str): 目标文件夹路径
    """
    # 创建目标文件夹（如果不存在）
    Path(target_folder).mkdir(parents=True, exist_ok=True)

    # 统计转换文件数量
    converted_count = 0

    # 遍历源文件夹中的所有文件
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            # 检查是否为HTML文件
            if file.lower().endswith((".html", ".htm")):
                # 构建源文件路径
                source_file_path = os.path.join(root, file)

                # 读取HTML文件
                try:
                    with open(source_file_path, "r", encoding="utf-8") as f:
                        html_content = f.read()
                except UnicodeDecodeError:
                    # 如果UTF-8解码失败，尝试其他编码
                    try:
                        with open(source_file_path, "r", encoding="gbk") as f:
                            html_content = f.read()
                    except UnicodeDecodeError:
                        print(f"无法解码文件: {source_file_path}")
                        continue

                # 转换为微信格式
                wechat_html_content = convert_html_to_wechat_format(html_content)

                # 计算相对于源文件夹的路径
                relative_path = os.path.relpath(source_file_path, source_folder)
                # 生成目标文件路径，保持目录结构
                target_file_path = os.path.join(
                    target_folder, os.path.splitext(relative_path)[0] + "_wechat.html"
                )

                # 创建目标文件的目录（如果不存在）
                target_file_dir = os.path.dirname(target_file_path)
                Path(target_file_dir).mkdir(parents=True, exist_ok=True)

                # 写入转换后的HTML文件
                with open(target_file_path, "w", encoding="utf-8") as f:
                    f.write(wechat_html_content)

                print(f"已转换: {source_file_path} -> {target_file_path}")
                converted_count += 1

    print(f"\n转换完成! 共转换 {converted_count} 个文件。")
    print(f"源文件夹: {source_folder}")
    print(f"目标文件夹: {target_folder}")


# 执行批量转换
if __name__ == "__main__":
    # 指定源文件夹和目标文件夹
    source_folder = r"C:\Users\admin\Desktop\新建文件夹 (3)"
    target_folder = r"C:\Users\admin\Desktop\微信公众号格式文件"

    # 执行批量转换
    batch_convert_html_files(source_folder, target_folder)
