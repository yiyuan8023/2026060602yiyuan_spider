import io
import json
import os

import ddddocr  # ocr
import requests
from PIL import ImageFont, Image, ImageDraw  # 用于处理图像

from retrying import retry  # 重试
import subprocess
from functools import partial  # 用来固定某个参数的固定值
from fontTools.ttLib import TTFont

from cookie_manager.extra_cookie import get_ramdom_ua
from extra.logger_ import logger

subprocess.Popen = partial(subprocess.Popen, encoding="utf-8")
# 解决execjs执行js时产生的乱码报错，需要在导入execjs模块之前，让Popen的encoding参数锁定为utf-8

import execjs  # PyExecJS  # noqa


class PddBaseApi(object):
    def __init__(self):
        # 获取当前Python文件所在的目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 构建anti_content.js的完整路径
        js_file_path = os.path.join(current_dir, "anti_content.js")
        print(js_file_path)

        with open(js_file_path, "r", encoding="utf8") as js_file:
            self.context = execjs.compile(js_file.read())

    def get_anti_content(self):
        """
        获取anti_content参数
        :return:
        """
        anti_content = self.context.call("get_anti_content")
        return anti_content

    @logger.catch
    def get_web_spider_rule(self):
        """
        获取web_spider_rule参数和ttf字体链接
        :return:
        """
        api = "https://api.yangkeduo.com/api/phantom/web/en/ft"
        payload = json.dumps({"scene": "cp_b_data_center"})

        res = requests.post(
            url=api, data=payload, headers={"User-Agent": get_ramdom_ua()}
        )
        # req_log(res)
        if res.status_code == 200:
            logger.info(json.dumps(res.json(), ensure_ascii=False))
            return {
                "web_spider_rule": res.json().get("web_spider_rule", None),
                "ttf_url": res.json().get("ttf_url", None),
            }
        else:
            return None

    @logger.catch
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def get_font_mapping(self, ttf_url):
        """
        解析出ttf中字体的映射关系
        :param ttf_url:
        :return:
        """
        io_ = io.BytesIO(
            requests.get(url=ttf_url, headers={"User-Agent": get_ramdom_ua()}).content
        )
        font = TTFont(io_)
        ocr = ddddocr.DdddOcr()
        uni_list = font.getGlyphOrder()[2:]
        char_list = []
        char_k_list = []
        io_.seek(0)
        font = ImageFont.truetype(io_, 40)
        # 将10个uni字符画到im，进而使用ocr识别获得对应数字
        for uchar in uni_list:
            unknown_char = f"\\u{uchar[3:]}".encode("utf8").decode("unicode_escape")
            im = Image.new(mode="RGB", size=(42, 40), color="white")
            draw = ImageDraw.Draw(im=im)
            draw.text(xy=(0, 0), text=unknown_char, fill=0, font=font)
            img_byte = io.BytesIO()
            im.save(img_byte, format="JPEG")
            h_ = uchar[3:].lower()
            char_k_list.append(r"\u" + h_)
            char_list.append(ocr.classification(img_byte.getvalue()))
        font_dict = dict(zip(char_k_list, char_list))
        logger.info(f"字体映射关系:{json.dumps(font_dict)}")
        return font_dict
