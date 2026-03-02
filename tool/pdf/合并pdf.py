#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PDF 合并工具（支持中文、半透明水印、页码、页眉页脚、图片水印）
自动处理页面旋转，适用于 PyMuPDF 1.18.0 及以上版本
但兼容较旧版本（不使用 csRGBA 和 fontname 参数）
"""

import os
import fitz
from extra.logger_ import logger  # 若没有该模块，可替换为 print


def add_text_to_page(
    page,
    text,
    position,
    fontname="china-ss",
    fontsize=12,
    color=(0, 0, 0),
    align=0,
    opacity=1.0,
    rotate_angle=0,
):
    """
    向页面添加文本（支持任意角度旋转）- 兼容旧版本
    :param page: fitz.Page 对象
    :param text: 要添加的文本内容
    :param position: (x, y) 文本位置坐标
    :param fontname: 字体名称，默认为 "china-ss"（宋体）
    :param fontsize: 字体大小，默认12
    :param color: RGB颜色值，默认黑色(0,0,0)
    :param align: 对齐方式：0=左对齐，1=居中，2=右对齐
    :param opacity: 透明度，0.0~1.0，默认不透明
    :param rotate_angle: 文本旋转角度（任意角度，单位：度）
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
        page.insert_text(
            (x, y), text, fontsize=fontsize, fontname=fontname, color=color
        )


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


def merge_pdfs_with_features(
    folder_path,
    output_path,
    add_page_numbers=True,
    watermark_text=None,
    header_text=None,
    footer_text=None,
    image_watermark_path=None,
    image_watermark_scale=0.5,
    image_watermark_opacity=0.5,
):
    """
    主函数：合并 PDF 并添加页码、水印、页眉页脚、图片水印
    """
    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"文件夹不存在：{folder_path}")

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"创建输出目录：{output_dir}")

    pdf_files = []
    for file in sorted(os.listdir(folder_path)):
        if file.lower().endswith(".pdf"):
            pdf_files.append(os.path.join(folder_path, file))

    if not pdf_files:
        logger.warning("文件夹中没有找到 PDF 文件")
        return

    logger.info(f"找到 {len(pdf_files)} 个 PDF 文件，开始合并...")
    merged_doc = fitz.open()

    for pdf_path in pdf_files:
        try:
            doc = fitz.open(pdf_path)
            merged_doc.insert_pdf(doc)
            doc.close()
            logger.info(f"已合并：{os.path.basename(pdf_path)}")
        except Exception as e:
            logger.error(f"合并 {pdf_path} 时出错：{e}")

    total_pages = len(merged_doc)
    logger.info(f"合并完成，总页数：{total_pages}")

    # ---------- 预处理图片水印（若提供） ----------
    img_pix = None
    aspect = 1.0
    if image_watermark_path and os.path.isfile(image_watermark_path):
        img_pix, aspect = load_image_with_alpha(
            image_watermark_path, image_watermark_opacity
        )

    # ---------- 遍历每一页，添加元素 ----------
    for page_num in range(total_pages):
        page = merged_doc[page_num]
        rect = page.rect
        width, height = rect.width, rect.height

        # 页码（页脚居中）
        if add_page_numbers:
            page_text = f"{page_num + 1} / {total_pages}"
            x_center = width / 2
            y_bottom = height - 10
            add_text_to_page(
                page,
                page_text,
                (x_center, y_bottom),
                fontsize=10,
                color=(0, 0, 0),
                align=2,
                rotate_angle=90,
                fontname="helv",
            )

        # 顶部水印
        if header_text:
            x = 5
            y = height - 20
            add_text_to_page(
                page,
                header_text,
                (x, y),
                fontsize=8,
                color=(0.7, 0.7, 0.7),
                opacity=0.6,
                align=0,
                rotate_angle=90,
            )

        # 底部水印
        if footer_text:
            x = 5
            y = height - 5

            add_text_to_page(
                page,
                footer_text,
                (x, y),
                fontsize=8,
                color=(0.7, 0.7, 0.7),
                opacity=0.6,
                align=0,
                rotate_angle=90,
            )

        # 图片水印（右上角）- 使用兼容方法
        if img_pix is not None:
            try:
                # 计算缩放后的尺寸，保持纵横比
                target_width = width * image_watermark_scale
                target_height = target_width * aspect

                # 右上角位置：x = width - target_width, y = height - target_height
                x = width - target_width - 5
                y = height - target_height - 5
                # y = 5
                img_rect = fitz.Rect(x, y, x + target_width, y + target_height)

                # 对于旧版本，使用简单的 insert_image
                page.insert_image(img_rect, pixmap=img_pix, overlay=True)
                logger.debug(f"第 {page_num + 1} 页插入图片水印成功")
            except Exception as e:
                logger.error(f"第 {page_num + 1} 页插入图片水印失败：{e}")

    merged_doc.save(output_path)
    merged_doc.close()
    logger.info(f"处理完成，输出文件：{output_path}")
    return merged_doc


if __name__ == "__main__":
    # 使用示例（请修改为你的实际路径）
    input_folder = r"C:\Users\admin\Desktop\PDF合并"
    output_file = r"C:\Users\admin\Desktop\PDF合并\输出\A.pdf"
    _image_watermark_path = r"C:\Users\admin\Desktop\PDF合并\公众号&微信.png"

    merge_pdfs_with_features(
        folder_path=input_folder,
        output_path=output_file,
        add_page_numbers=True,
        header_text="关注公众号获取最新文件,本次更新：26年2月24日",  # 页眉
        footer_text="公众号：一元福寿康;微信号：W735531994",  # 页脚
        image_watermark_path=_image_watermark_path,  # 图片水印路径
        image_watermark_scale=0.2,  # 图片宽度占页面宽度的20%
        image_watermark_opacity=0.5,  # 透明度50%
    )
