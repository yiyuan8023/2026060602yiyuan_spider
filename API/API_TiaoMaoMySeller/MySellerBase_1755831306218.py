# batch_html_to_markdown.py
import os
from pathlib import Path
import re
from html.parser import HTMLParser

class HTMLToMarkdownConverter(HTMLParser):
    def __init__(self):
        super().__init__()
        self.markdown = []
        self.lists = []  # 跟踪列表层级
        self.list_counters = []  # 跟踪有序列表计数器
        self.in_pre = False  # 是否在<pre>标签内
        self.in_table = False  # 是否在<table>标签内
        self.table_rows = []  # 存储表格行
        self.current_row = []  # 当前表格行
        self.header_level = 0  # 标题级别
        self.link_href = ""  # 存储链接地址
        self.in_link = False  # 是否在链接标签内
        self.should_add_linebreak = False  # 是否需要添加换行
        self.current_tag = ""  # 当前处理的标签

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        self.current_tag = tag

        # 处理标题标签
        if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            self.header_level = int(tag[1])
            self.markdown.append('\n' + '#' * self.header_level + ' ')

        # 处理段落
        elif tag == 'p':
            if self.markdown and not self.markdown[-1].endswith('\n\n') and len(self.markdown) > 0:
                self.markdown.append('\n\n')

        # 处理换行
        elif tag == 'br':
            self.markdown.append('  \n')

        # 处理粗体
        elif tag in ['strong', 'b']:
            self.markdown.append('**')

        # 处理斜体
        elif tag in ['em', 'i']:
            self.markdown.append('*')

        # 处理删除线
        elif tag in ['del', 's']:
            self.markdown.append('~~')

        # 处理行内代码
        elif tag == 'code' and not self.in_pre:
            self.markdown.append('`')

        # 处理代码块
        elif tag == 'pre':
            self.in_pre = True
            if self.markdown and len(self.markdown) > 0 and not self.markdown[-1].endswith('\n'):
                self.markdown.append('\n')
            self.markdown.append('\n')

        # 处理链接
        elif tag == 'a':
            self.markdown.append(f']({self.link_href})')
            self.in_link = False
            self.link_href = ""

        # 处理引用
        elif tag == 'blockquote':
            self.markdown.append('\n')

        # 处理列表
        elif tag in ['ul', 'ol']:
            if self.lists:
                self.lists.pop()
                self.list_counters.pop()
            if not self.lists:  # 所有列表结束
                self.markdown.append('\n')
        elif tag == 'li':
            self.markdown.append('\n')

        # 处理表格
        elif tag == 'table':
            self.in_table = False
            # 生成表格markdown
            if self.table_rows:
                self._generate_table_markdown()
        elif tag == 'tr' and self.in_table:
            self.table_rows.append(self.current_row.copy())
        elif tag in ['th', 'td'] and self.in_table:
            pass  # 内容在handle_data中处理

    def handle_data(self, data):
        if not data.strip() and not self.in_pre:
            return

        # 表格数据特殊处理
        if self.in_table and not self.in_pre:
            self.current_row.append(data.strip())
            return

        # 一般数据处理
        if not self.in_pre:
            # 只有在非链接且非表格状态下才转义特殊字符
            if not (self.in_link and self.current_tag == 'a'):
                # 转义特殊字符，但避免重复转义
                data = re.sub(r'([\\\*`_{}[\]()#+\-.!])', r'\\\1', data)
            # 处理多个空格，但不在代码块中处理
            data = re.sub(r'[ \t]+', ' ', data)

        self.markdown.append(data)

    def _generate_table_markdown(self):
        if not self.table_rows:
            return

        # 添加空行
        if self.markdown and not self.markdown[-1].endswith('\n\n'):
            self.markdown.append('\n')

        # 如果没有行，直接返回
        if not self.table_rows:
            return

        # 创建表格
        for i, row in enumerate(self.table_rows):
            # 添加表格行
            markdown_row = '| ' + ' | '.join(cell for cell in row) + ' |'
            self.markdown.append(markdown_row + '\n')

            # 如果是表头，添加分隔行
            if i == 0:
                separator = '|' + '|'.join(' --- ' for _ in row) + '|'
                self.markdown.append(separator + '\n')

    def get_markdown(self):
        result = ''.join(self.markdown)
        # 清理多余的空行，但保留代码块中的空行
        result = re.sub(r'\n{3,}', '\n\n', result)
        # 去除首尾空白
        result = result.strip()
        return result

def convert_html_to_markdown(html_content):
    """
    将HTML内容转换为Markdown

    Args:
        html_content (str): HTML内容字符串

    Returns:
        str: Markdown格式字符串
    """
    converter = HTMLToMarkdownConverter()
    converter.feed(html_content)
    return converter.get_markdown()

def batch_convert_html_to_markdown(source_folder, target_folder):
    """
    批量将文件夹中的HTML文件转换为Markdown文件

    Args:
        source_folder (str): 源文件夹路径，包含HTML文件
        target_folder (str): 目标文件夹路径，用于保存Markdown文件
    """
    # 创建目标文件夹（如果不存在）
    Path(target_folder).mkdir(parents=True, exist_ok=True)

    # 统计转换文件数量
    converted_count = 0

    # 遍历源文件夹中的所有文件
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            # 检查是否为HTML文件
            if file.lower().endswith(('.html', '.htm')):
                # 构建源文件路径
                source_file_path = os.path.join(root, file)

                # 读取HTML文件
                try:
                    with open(source_file_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                except UnicodeDecodeError:
                    # 如果UTF-8解码失败，尝试其他编码
                    try:
                        with open(source_file_path, 'r', encoding='gbk') as f:
                            html_content = f.read()
                    except UnicodeDecodeError:
                        print(f"无法解码文件: {source_file_path}")
                        continue

                # 转换为Markdown
                markdown_content = convert_html_to_markdown(html_content)

                # 计算相对于源文件夹的路径
                relative_path = os.path.relpath(source_file_path, source_folder)
                # 生成目标文件路径，保持目录结构
                target_file_path = os.path.join(
                    target_folder,
                    os.path.splitext(relative_path)[0] + '.md'
                )

                # 创建目标文件的目录（如果不存在）
                target_file_dir = os.path.dirname(target_file_path)
                Path(target_file_dir).mkdir(parents=True, exist_ok=True)

                # 写入Markdown文件
                with open(target_file_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)

                print(f"已转换: {source_file_path} -> {target_file_path}")
                converted_count += 1

    print(f"\n转换完成! 共转换 {converted_count} 个文件。")
    print(f"源文件夹: {source_folder}")
    print(f"目标文件夹: {target_folder}")

# 使用示例
if __name__ == "__main__":
    # 指定源文件夹和目标文件夹
    source_folder = r"C:\Users\admin\Desktop\新建文件夹 (3)"
    target_folder = r"C:\Users\admin\Desktop\转换后的Markdown文件"

    # 执行批量转换
    batch_convert_html_to_markdown(source_folder, target_folder)
