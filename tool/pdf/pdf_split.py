import PyPDF2
import os


def split_pdf(input_pdf_path, pages_per_split=900):
    # 获取原文件名（不含扩展名）
    base_name = os.path.splitext(os.path.basename(input_pdf_path))[0]

    # 创建与输入文件同名的文件夹
    output_dir = os.path.join(os.path.dirname(input_pdf_path), base_name)
    os.makedirs(output_dir, exist_ok=True)  # 如果文件夹已存在，则不会报错

    # 打开原始PDF文件
    with open(input_pdf_path, "rb") as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        total_pages = len(pdf_reader.pages)

        # 计算需要拆分成多少个文件
        num_splits = (total_pages + pages_per_split - 1) // pages_per_split

        for i in range(num_splits):
            # 创建一个新的PDF写入对象
            pdf_writer = PyPDF2.PdfWriter()

            # 计算当前拆分的起始和结束页码
            start_page = i * pages_per_split
            end_page = min(start_page + pages_per_split, total_pages)

            # 将指定范围的页面添加到新的PDF中
            for page_num in range(start_page, end_page):
                pdf_writer.add_page(pdf_reader.pages[page_num])

            # 生成新文件名
            output_filename = f"{base_name}_part_{i + 1}.pdf"
            output_path = os.path.join(output_dir, output_filename)  # 完整输出路径

            # 写入新的PDF文件
            with open(output_path, "wb") as output_pdf:
                pdf_writer.write(output_pdf)

            print(f"已生成文件: {output_path}")


# 使用示例
input_pdf = r"C:\Users\admin\Desktop\pdf\段永平博客文章合集(2006-2018).pdf"  # 替换为你的PDF文件路径
split_pdf(input_pdf, pages_per_split=500)
