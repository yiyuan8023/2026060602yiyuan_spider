# from fontTools.ttLib import TTFont
#
#
# def get_font_data():
#     font_dict = {}
#     # font = TTFont("file.woff")
#     font = TTFont(r"C:\Users\OYH\Desktop\aaaa.ttf")
#     uni_list = font.getGlyphOrder()[2:]
#     print(uni_list)
#     cmap = font.get("cmap").getBestCmap()
#     for k, v in cmap.items():
#         # print(k,v)
#         if v[3:] and v=="uniE8DD":
#             print(k,v)
#             content = "\\u00" + v[3:] if len(v[3:]) == 2 else "\\u" + v[3:]
#             real_content = content.encode('utf-8').decode('unicode_escape')
#             k_hex = hex(k)
#             # 网页返回的字体是以&#x开头  ，换成以这个开头，下面代码就是直接替换
#             real_k = k_hex.replace("0x", "&#x")
#             font_dict[real_k] = real_content
#     # print(font_dict)
#     return font_dict
# get_font_data()
# from PIL import ImageFont, Image, ImageDraw
# import io
# import ddddocr as ddddocr
# def get_font_data2():
#     ocr = ddddocr.DdddOcr()
#     font_dict = {}
#     # font = TTFont("file.woff")
#     font = TTFont(r"C:\Users\OYH\Desktop\aaaa.ttf")
#     uni_list = font.getGlyphOrder()[2:]
#     char_list = []
#     char_k_list=[]
#     font = ImageFont.truetype(r"C:\Users\OYH\Desktop\aaaa.ttf", 40)
#     # 将10个uni字符画到im，进而使用ocr识别获得对应数字
#     for uchar in uni_list:
#
#         unknown_char = f"\\u{uchar[3:]}".encode("utf8").decode("unicode_escape")
#         im = Image.new(mode='RGB', size=(42, 40), color="white")
#         draw = ImageDraw.Draw(im=im)
#         draw.text(xy=(0, 0), text=unknown_char, fill=0, font=font)
#         img_byte = io.BytesIO()
#         im.save(img_byte, format='JPEG')
#         char_k_list.append(r"\u"+f"{uchar[3:]}".lower())
#         # print(type(img_byte.getvalue()))
#         char_list.append(ocr.classification(img_byte.getvalue()))
#     font_dict = dict(zip(char_k_list, char_list))
#     print("字体映射关系:", font_dict)
# get_font_data2()