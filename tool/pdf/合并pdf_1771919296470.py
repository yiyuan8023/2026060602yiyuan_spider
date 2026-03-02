#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PDF 合并工具（支持中文、半透明水印、页码、页眉页脚、图片水印、目录超链接）
自动处理页面旋转，适用于 PyMuPDF 1.18.0 及以上版本
但兼容较旧版本（不使用 csRGBA 和 fontname 参数）
"""

import os
import fitz
import math
from extra.logger_ import logger  # 若没有该模块，可替换为 print


def add_text_to_page(page, text, position, fontname="china-ss", fontsize=12, color=(0, 0, 0),
                     align=0, opacity=1.0, rotate_angle=0):
    """
    向页面添加文本（支持任意角度旋转）- 兼容旧版本
    """
    x, y = position

    # 估算文本宽度用于对齐计算（粗略估算）
    text_width = fontsize * len(text) * 0.5

    if align == 1:  # 居中对齐
        x -= text_width / 2
    elif align == 2:  # 右对齐
        x -= text_width

    # 抵消页面旋转影响
    page_rotation = -page.rotation if page.rotation != 0 else 0
    total_rotate_angle = page_rotation + rotate_angle

    # 对于旧版本 PyMuPDF，使用较简单的方法
    try:
        # 尝试新版本的 TextWriter 方法（不带 fontname 参数）
        tw = fitz.TextWriter(page.rect, opacity=opacity, color=color)
        # 创建旋转矩阵（如果支持）
        matrix = None
        if total_rotate_angle != 0:
            try:
                matrix = fitz.Matrix(total_rotate_angle, total_rotate_angle)
            except:
                matrix = None

        # 尝试不带 fontname 参数
        if matrix:
            tw.append((x, y), text, fontsize=fontsize, matrix=matrix)
        else:
            tw.append((x, y), text, fontsize=fontsize)

        tw.write_text(page, color=color, opacity=opacity)
    except:
        # 如果 TextWriter 也不支持，回退到旧版 insert_text
        # 旧版不支持旋转和透明度
        page.insert_text((x, y), text,
                         fontsize=fontsize,
                         fontname=fontname,
                         color=color)


def load_image_with_alpha(image_path, opacity):
    """
    加载图片并创建带 alpha 通道的 Pixmap（兼容旧版本）
    """
    try:
        # 加载原始图片
        raw_pix = fitz.Pixmap(image_path)

        # 对于旧版本，直接使用原始图片，不处理透明度
        # 因为透明度可能不支持
        logger.info(f"图片加载成功：{image_path}，但透明度可能不完全支持")
        return raw_pix, raw_pix.height / raw_pix.width

    except Exception as e:
        logger.error(f"图片加载失败：{e}")
        return None, 1.0


def create_toc_pages(doc, pdf_files, page_offsets, title="目录", items_per_page=20):
    """
    创建目录页（支持多页）并添加超链接

    :param doc: PDF文档对象
    :param pdf_files: PDF文件路径列表
    :param page_offsets: 每个文件的起始页码偏移量字典
    :param title: 目录标题
    :param items_per_page: 每页显示的目录项数量
    :return: 目录页数量
    """
    total_files = len(pdf_files)
    total_pages_needed = math.ceil(total_files / items_per_page)

    logger.info(f"需要创建 {total_pages_needed} 页目录（共 {total_files} 个文件，每页 {items_per_page} 项）")

    toc_pages = []

    for page_idx in range(total_pages_needed):
        # 创建新页面作为目录页（A4尺寸）
        toc_page = doc.new_page(width=595, height=842)
        toc_pages.append(toc_page)

        # 添加标题（第一页显示完整标题，后续页显示"目录(续)"）
        title_y = 80
        if page_idx == 0:
            page_title = title
        else:
            page_title = f"{title} (续)"

        add_text_to_page(toc_page, page_title, (297, title_y),
                         fontsize=24, color=(0, 0, 0.8), align=1)

        # 添加页码提示
        add_text_to_page(toc_page, f"第 {page_idx + 1} 页 / 共 {total_pages_needed} 页",
                         (297, title_y + 30), fontsize=10, color=(0.5, 0.5, 0.5), align=1)

        # 添加分割线
        line_y = title_y + 50
        toc_page.draw_line((50, line_y), (545, line_y), color=(0.7, 0.7, 0.7), width=1)

        # 计算当前页要显示的目录项范围
        start_idx = page_idx * items_per_page
        end_idx = min(start_idx + items_per_page, total_files)

        # 添加目录项
        y_start = line_y + 30
        line_height = 28

        for local_idx in range(start_idx, end_idx):
            file_idx = local_idx
            y_pos = y_start + (local_idx - start_idx) * line_height

            pdf_path = pdf_files[file_idx]
            filename = os.path.basename(pdf_path).

            # 正文页码从1开始计算（忽略目录页）
            start_page = page_offsets[pdf_path] + 1  # +1 因为正文页码从1开始

            # 计算结束页码
            if file_idx < total_files - 1:
                next_pdf = pdf_files[file_idx + 1]
                end_page = page_offsets[next_pdf]
            else:
                # 最后一个文件，需要计算总正文页数
                # 总页数 = 文档总页数 - 目录页数
                total_content_pages = len(doc) - total_pages_needed
                end_page = total_content_pages

            # 格式化显示
            display_text = f"{file_idx + 1}. {filename}"

            # 添加文件名文本
            add_text_to_page(toc_page, display_text, (70, y_pos),
                             fontsize=11, color=(0, 0, 0.6), align=0)

            # 添加超链接矩形区域（点击跳转到对应PDF的第一页）
            link_rect = fitz.Rect(50, y_pos - 12, 450, y_pos + 10)

            # 创建超链接到对应页面的顶部
            # 注意：跳转页码需要加上目录页数
            target_page = start_page - 1 + total_pages_needed  # 加上目录页偏移
            toc_page.insert_link({
                "kind": fitz.LINK_GOTO,
                "from": link_rect,
                "page": target_page,
                "to": fitz.Point(0, 0)  # 跳转到页面顶部
            })

            # 添加页码范围靠右显示
            page_range_text = f"第 {start_page}-{end_page} 页"
            add_text_to_page(toc_page, page_range_text, (500, y_pos),
                             fontsize=9, color=(0.5, 0.5, 0.5), align=2)

        # 如果不是最后一页，添加"下一页"提示
        if page_idx < total_pages_needed - 1:
            add_text_to_page(toc_page, "↓ 下一页继续", (297, 800),
                             fontsize=10, color=(0.5, 0.5, 0.5), align=1)

    return total_pages_needed


def merge_pdfs_with_features(folder_path,
                             output_path,
                             add_page_numbers=True,
                             watermark_text=None,
                             header_text=None,
                             footer_text=None,
                             image_watermark_path=None,
                             image_watermark_scale=0.2,
                             image_watermark_opacity=0.5,
                             add_toc=True,
                             toc_title="目录",
                             toc_items_per_page=20):
    """
    主函数：合并 PDF 并添加页码、水印、页眉页脚、图片水印、目录超链接
    """
    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"文件夹不存在：{folder_path}")

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"创建输出目录：{output_dir}")

    # 获取所有PDF文件并排序
    pdf_files = []
    for file in sorted(os.listdir(folder_path)):
        if file.lower().endswith('.pdf'):
            pdf_files.append(os.path.join(folder_path, file))

    if not pdf_files:
        logger.warning("文件夹中没有找到 PDF 文件")
        return

    logger.info(f"找到 {len(pdf_files)} 个 PDF 文件，开始合并...")

    # 创建新文档
    merged_doc = fitz.open()

    # 如果需要目录，先创建目录页占位（但还不知道需要多少页）
    toc_page_count = 0
    if add_toc:
        # 先合并文件，计算页码后再创建目录
        logger.info("先合并PDF文件，稍后创建目录...")

    # 记录每个文件的起始页码（不考虑目录页，从0开始）
    page_offsets = {}
    current_page = 0

    # 先合并所有PDF文件并记录页码偏移
    for pdf_path in pdf_files:
        try:
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            page_offsets[pdf_path] = current_page
            merged_doc.insert_pdf(doc)
            current_page += page_count
            doc.close()
            logger.info(f"已合并：{os.path.basename(pdf_path)} (共 {page_count} 页)")
        except Exception as e:
            logger.error(f"合并 {pdf_path} 时出错：{e}")

    content_page_count = current_page
    logger.info(f"正文合并完成，共 {content_page_count} 页")

    # 如果需要目录，现在创建目录页
    if add_toc:
        # 创建目录页（插入到文档开头）
        # 注意：new_page 默认插入到文档末尾，所以我们需要记录当前页数
        # 先记录当前文档大小
        current_doc_size = len(merged_doc)

        # 计算需要多少页目录
        toc_page_count = create_toc_pages(
            merged_doc,
            pdf_files,
            page_offsets,
            title=toc_title,
            items_per_page=toc_items_per_page
        )

        # 将刚刚创建的目录页移动到文档开头
        # 新创建的页面在末尾，我们需要将它们移动到开头
        for i in range(toc_page_count):
            # 将最后一页移动到开头
            merged_doc.move_page(len(merged_doc) - 1, i)

        logger.info(f"目录页创建完成，共 {toc_page_count} 页，已移动到文档开头")

        # 重新计算总页数
        total_pages = len(merged_doc)
        logger.info(f"最终文档总页数：{total_pages}（包含 {toc_page_count} 页目录）")
    else:
        total_pages = content_page_count
        toc_page_count = 0

    # ---------- 预处理图片水印（若提供） ----------
    img_pix = None
    aspect = 1.0
    if image_watermark_path and os.path.isfile(image_watermark_path):
        img_pix, aspect = load_image_with_alpha(image_watermark_path, image_watermark_opacity)

    # ---------- 遍历每一页，添加元素 ----------
    for page_num in range(total_pages):
        page = merged_doc[page_num]
        rect = page.rect
        width, height = rect.width, rect.height

        # 判断是否为目录页
        is_toc_page = page_num < toc_page_count

        # 页码（目录页不加页码，正文页码从1开始）
        if add_page_numbers and not is_toc_page:
            # 正文页码 = 当前页码 - 目录页数 + 1
            content_page_number = page_num - toc_page_count + 1
            page_text = f"{content_page_number} / {content_page_count}"
            x_center = width / 2
            y_bottom = height - 50
            add_text_to_page(page, page_text, (x_center, y_bottom),
                             fontsize=10, color=(0, 0, 0), align=2, rotate_angle=90, fontname="helv")

        # 顶部水印（目录页不加）
        if header_text and not is_toc_page:
            x = 5
            y = height - 20
            add_text_to_page(page, header_text, (x, y),
                             fontsize=8, color=(0.7, 0.7, 0.7),
                             opacity=0.6, align=0, rotate_angle=90)

        # 底部水印（目录页不加）
        if footer_text and not is_toc_page:
            x = 5
            y = height - 5
            add_text_to_page(page, footer_text, (x, y),
                             fontsize=8, color=(0.7, 0.7, 0.7),
                             opacity=0.6, align=0, rotate_angle=90)

        # 图片水印（右上角）- 目录页不加
        if img_pix is not None and not is_toc_page:
            try:
                # 计算缩放后的尺寸，保持纵横比
                target_width = width * image_watermark_scale
                target_height = target_width * aspect

                # 右上角位置：x = width - target_width, y = height - target_height
                x = width - target_width - 5
                y = height - target_height - 5
                img_rect = fitz.Rect(x, y, x + target_width, y + target_height)

                # 对于旧版本，使用简单的 insert_image
                page.insert_image(img_rect, pixmap=img_pix, overlay=True)
                if page_num % 10 == 0:  # 每10页记录一次，避免日志过多
                    logger.debug(f"第 {page_num + 1} 页插入图片水印成功")
            except Exception as e:
                logger.error(f"第 {page_num + 1} 页插入图片水印失败：{e}")

    merged_doc.save(output_path)
    merged_doc.close()
    logger.info(f"处理完成，输出文件：{output_path}")
    return merged_doc


if __name__ == "__main__":
    # 使用示例（请修改为你的实际路径）
    input_folder = r"C:\Users\admin\Desktop\公众号PDF2026"
    output_file = r"C:\Users\admin\Desktop\公众号PDF2026\输出\20260224一元福寿康公众号文章整理.pdf"
    _image_watermark_path = r"C:\Users\admin\Desktop\PDF合并\公众号&微信.png"

    merge_pdfs_with_features(
        folder_path=input_folder,
        output_path=output_file,
        add_page_numbers=True,
        header_text="关注公众号获取最新文件,本次更新：26年2月24日",  # 页眉
        footer_text="公众号：一元福寿康;微信号：W735531994",  # 页脚
        image_watermark_path=_image_watermark_path,  # 图片水印路径
        image_watermark_scale=0.25,  # 图片宽度占页面宽度的15%
        image_watermark_opacity=0.5,  # 透明度50%
        add_toc=True,  # 添加目录
        toc_title="文件目录",  # 目录标题
        toc_items_per_page=20  # 每页显示20个目录项
    )