#!/usr/bin/env python
# -*- coding: utf-8 -*-
import operator
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from html.parser import HTMLParser
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from lcypytools import common
import bs4, urllib
from pyquery import PyQuery as pq
from lcypytools.common import Timer

import setting

"""
1、检测页面中是否存在form，存在则让用户选择是否具有搜索筛选功能，如果是，进行筛选包装。
2、自动检测页面中的所有form，以及form中所有的字段名字和搜索按钮位置，并让用户指定是哪个form，字段里填写什么，哪个是真正的搜索按钮，注意required。
3、模拟填写和点击搜索按钮，同时不要忘了得到输入框的位置信息（selector），然后用selenium找到当前弹出的页面，并进行页面解析。
4、让用户选择主要信息区域，和之前相同。
5、包装成服务，同时告诉后台爬虫模块输入框和搜索按钮的位置，以及结果字段的位置，供后台使用。
"""


class Form:
    def __init__(self, log):
        options = Options()
        options.binary_location = setting.CHROME_BINARY_LOCATION
        options.add_argument('--headless')  # 不显示浏览器
        self.browser = webdriver.Chrome(chrome_options=options, executable_path=setting.DRIVER_PATH)
        # self.browser.set_window_size(setting.SCREEN_WIDTH, 800)  # set the window size that you need
        self.parser = HTMLParser()
        self.log = log

    def __crawler(self):
        self.browser.set_page_load_timeout(60)  # 最长等待时间
        try:
            self.browser.get(self.url)
            time.sleep(3)  # 强行等待3s
        except TimeoutException:
            self.log.write_without_datetime("503 " + "request time out,task end,please retry")
            self.browser.quit()
            exit(-1)
        self.document_size = len(self.browser.page_source)
        self.document_tree_length = self.browser.execute_script("return document.getElementsByTagName('*').length")
        self.page = pq(self.browser.page_source.replace('xmlns', 'another_attr'))  # pyquery
        self.soup = BeautifulSoup(self.browser.page_source, 'html.parser')  # 标准库方式载入页面源代码
        try:
            self.page_height = self.browser.find_element_by_tag_name("body").rect["height"]  # 找到body大小
            self.browser.set_window_size(setting.SCREEN_WIDTH, self.page_height)  # 设置窗口大小
        except:
            pass
        """
        mark
        """
        self.browser.save_screenshot(self.output_folder + "/screenshot.png")  # 截屏

    def segment(self, url, output_folder="output", is_output_images=False):
        self.url = url
        self.output_folder = self.remove_slash(output_folder)  # 去除冗余信息后得到的路径

        self.time_crawl = Timer("crawl_form_page")
        self.log.write("Crawl HTML Document from %s,please wait for about 40s(max 60s)" % self.url)
        self.__crawler()  # 爬取页面
        self.time_crawl.end()

        self.time_find_form_and_generate_rules = Timer("find_form_and_generate_rules")
        self.log.write("Finding form lable on %s" % self.url)
        self.exist_form = self.__find_tag_form()  # 找到有没有form标签
        self.time_find_form_and_generate_rules.end()

        self.__get_form_pic()  # 生成form的区域截图
        self.__save_form_rules()

        self.log.write("Finished on  %s" % self.url)
        self.log.write_without_datetime(
            "200 " + setting.SERVER_ADDRESS + self.output_folder.replace("static",
                                                                         "statics") + "/form_list.json " + setting.SERVER_ADDRESS + self.output_folder + "/form_seg_shot.png")

    """
    通过下面的操作，程序得到了整个网页中所有的tag节点的信息，并按照广度优先搜索的顺序，存储到了self.allnodes列表中
    去除了类似注释，js，css等无用信息，以及空格和空行。
    同时，因为使用了beautiful soup，因此网页信息会自动容错。
    """

    def __find_tag_form(self):
        self.handleSpecialPageBefore()  # 针对性的对页面进行包装,给页面表单信息增加form标签
        form = self.soup.find_all("form")  # 查找页面中是否存在form标签
        form_t = []
        iframexx = self.soup.find_all("iframe")  # 查找位于iframe中的form
        for i in range(len(form)):
            form_t.append({"form": form[i], "type": 0, "css_selector": self.__get_css_selector(form[i]),"in_selector":self.__get_css_selector(form[i])})  # 普通form
        form_f = self.soup.find_all("input")
        for i in range(len(form_f)):
            selector_t = self.__get_css_selector(form_f[i]) # 临时selector，判断此item有没有在其他form中出现
            t = True
            for f in form_t:
                if selector_t.find(f["in_selector"])>=0:
                    t = False
                    break
            if t:
                selector = self.__get_css_selector(form_f[i], parents=2)  # 元素的上两级找起
                form_f[i] = form_f[i].parent.parent.parent
                form_t.append({"form": form_f[i], "type": 0,
                               "css_selector": selector,"in_selector":selector})
        self.form_list = []
        self.form_list_json = []
        for iframe in iframexx:
            css_selector = self.__get_css_selector(iframe)
            self.browser.switch_to.frame(self.browser.find_element_by_css_selector(css_selector))  # 切换到此iframe
            iframe_soup = BeautifulSoup(self.browser.page_source)
            form_f = iframe_soup.find_all("form")
            for i in range(len(form_f)):
                selector = self.__get_css_selector(form_f[i])
                form_t.append({"form": form_f[i], "type": 1,
                               "css_selector": css_selector + " >f> " + selector,"in_selector":selector})
            form_f = iframe_soup.find_all("input")
            for i in range(len(form_f)):
                selector_t = self.__get_css_selector(form_f[i])  # 临时selector，判断此item有没有在其他form中出现
                t = True
                for f in form_t:
                    if selector_t.find(f["in_selector"]) >= 0:
                        t = False
                        break
                if t:
                    form_f[i] = form_f[i].parent.parent.parent
                    selector = self.__get_css_selector(form_f[i], parents=2)  # 元素的上两级找起
                    form_t.append({"form": form_f[i], "type": 1,
                                   "css_selector": css_selector + " >f> " + selector,"in_selector":selector})

            self.browser.switch_to.default_content()  # 切换到默认页面

        for i in range(len(form_t)):
            if form_t[i]["type"] == 1:
                iframe = form_t[i]["css_selector"].split(">f>")[0]  # iframe的selector
                css_selector = form_t[i]["css_selector"].split(">f>")[1]  # 表格在iframe中的selector
                slot = 'return document.querySelector("' + iframe + '").contentWindow.'
                selector_slot = iframe + ">f> "
            else:
                css_selector = self.__get_css_selector(form_t[i]["form"])
                slot = "return "
                selector_slot = ""
            # print(slot + 'document.querySelector("' + css_selector + '")')
            try: # 存在iframe跨域问题则跳过
                exist = self.browser.execute_script(slot + 'document.querySelector("' + css_selector + '")')
            except:
                continue
            if exist == None:
                css_selector = css_selector.replace("> form", "")
            btn_sub = False
            index = 0
            btn_id = 1
            nokeynameid = 1
            input_list = []  # 输入input的位置所在
            submit_button_list = []  # 可能的提交按钮所在位置
            allnodes = [form_t[i]["form"]]  # put body block into allnodes list
            it = 0
            while len(allnodes) > it:
                for child in allnodes[it].children:
                    if isinstance(child, bs4.element.Tag):  # 如果直接子节点是TAG类型，则放入children列表，即得到正文中的所有显示出的信息（去除注释及其他代码）
                        allnodes.append(child)
                        try:
                            required = child.attrs["required"]
                        except:
                            required = False
                        try:
                            value = child.attrs["value"]
                        except:
                            value = ""
                        try:
                            name = child.attrs["name"]
                        except:
                            name = "no_key_name_" + str(nokeynameid)
                            nokeynameid += 1
                        css_selector_this = self.__get_css_selector(child)
                        # 下面三行用来判断如果此页面是经过加form后的页面，那么此处路径去除
                        try:  # 如果碰到类似asp这样奇怪的标签
                            exist = self.browser.execute_script(
                                slot + 'document.querySelector("' + css_selector_this + '")')
                        except:
                            continue  # 跳过即可
                        if exist == None:
                            css_selector_this = css_selector_this.replace("> form", "")
                        # 防止没有type属性
                        try:
                            ctype = child.attrs["type"]
                        except:
                            ctype = "text"

                        if child.name == "input" and (ctype == "checkbox" or ctype == "radio"):  # 对radio和checkbox单独处理
                            # if name.find("no_key_name") >= 0: # 有key才行
                            #     continue
                            try:
                                checked = self.browser.execute_script(
                                    slot + 'document.querySelector("' + css_selector_this + '").checked')
                            except:
                                checked = "false"
                            input_list.append({"id": index, "type": ctype, "name": name + "_" + value,
                                               "required": required, "css_selector": selector_slot + css_selector_this,
                                               "value": checked, "query_name": name + "_" + value, "description": "",
                                               "index": "T" + str(index + 1),
                                               "form_type": form_t[i]["type"]})  # 注意后端写法，根据value值选择是否选中！！！
                            index += 1
                            continue  # 处理完毕

                        if child.name == "select" or child.name == "datalist":
                            # self.browser.find_element_by_css_selector(css_selector_this)
                            selectedIndex = self.browser.execute_script(
                                slot + 'document.querySelector("' + css_selector_this + '").selectedIndex')  # 在页面上执行js代码，并获得selectindex
                            input_list.append({"id": index, "type": child.name, "name": name, "required": required,
                                               "css_selector": selector_slot + css_selector_this,
                                               "value": selectedIndex,
                                               "query_name": name, "description": "",
                                               "index": "T" + str(index + 1),
                                               "form_type": form_t[i]["type"]})  # 注意后端写法，根据value值选择是否选中！！！
                            index += 1
                            continue

                        if child.name == "input" and ctype != "hidden" and ctype!="reset" and ctype != "submit" and ctype != "button":
                            input_list.append(
                                {"id": index, "type": ctype, "name": name, "required": required,
                                 "css_selector": selector_slot + css_selector_this, "value": value, "query_name": name,
                                 "description": "", "index": "T" + str(index + 1), "form_type": form_t[i]["type"]})
                            index += 1
                        elif child.name == "input" and (
                                ctype == "submit" or ctype == "button"):
                            btn_sub = True  # 存在这种类型的button就不考虑其他类型的提交按钮形式了
                            submit_button_list.append(
                                {"id": btn_id - 1, "type": ctype, "name": name, "required": required,
                                 "css_selector": selector_slot + css_selector_this, "index": "b" + str(btn_id),
                                 "form_type": form_t[i]["type"]})  # 可能的提交按钮所在位置
                            btn_id += 1
                        elif child.name == "button":  # 所有的button都算上
                            btn_sub = True
                            submit_button_list.append(
                                {"id": btn_id - 1, "type": child.name,
                                 "css_selector": selector_slot + css_selector_this,
                                 "index": "b" + str(btn_id), "form_type": form_t[i]["type"]})  # 可能的提交按钮所在位置
                            btn_id += 1
                        elif not btn_sub and (child.name == "a" or child.name == "img"):  # 图片格式也有可能是提交按钮
                            submit_button_list.append(
                                {"id": btn_id - 1, "type": child.name,
                                 "css_selector": selector_slot + css_selector_this,
                                 "index": "b" + str(btn_id), "form_type": form_t[i]["type"]})  # 可能的提交按钮所在位置
                            btn_id += 1
                        elif child.name == "textarea":
                            input_list.append(
                                {"id": index, "type": "textarea", "name": name, "required": required,
                                 "css_selector": selector_slot + css_selector_this, "value": value, "query_name": name,
                                 "description": "", "index": "T" + str(index + 1), "form_type": form_t[i]["type"]})
                            index += 1

                it += 1
            if btn_sub:  # 存在button则删除可能存在的a元素
                for item in submit_button_list[:]:
                    if item["type"] == "a" or child.name == "img":
                        submit_button_list.remove(item)
            for j in range(len(submit_button_list)):
                submit_button_list[j]["index"] = "b" + str(j + 1)
            if len(submit_button_list) != 0: # 只保存有button的form
                self.form_list.append(
                    {"id": i, "main_btn_index": 0, "form": form_t[i]["form"], "len": len(form_t[i]["form"].contents),
                     "css_selector": selector_slot + css_selector, "input_list": input_list,
                     "submit_button_list": submit_button_list, "type": form_t[i]["type"]})
                self.form_list_json.append(
                    {"id": i, "main_btn_index": 0, "len": len(form_t[i]["form"].contents),
                     "css_selector": selector_slot + css_selector,
                     "input_list": input_list, "submit_button_list": submit_button_list, "type": form_t[i]["type"]})

        # for iframe in iframexx:
        #     css_selector = self.__get_css_selector(iframe)
        #     self.browser.execute_script('window.open("'+iframe.attrs['src']+'");') # 打开新标签页
        #     handles = self.browser.window_handles
        #     self.browser.switch_to.window(handles[-1])
        #     response = self.browser.page_source
        #     iframe_soup = BeautifulSoup(response)
        #     form_f = iframe_soup.find_all("form")
        #     for i in range(len(form_f)):
        #         selector = self.__get_css_selector(form_f[i])
        #         self.form_list.append({"form": form_f[i], "len": len(form_f[i].contents),"css_selector":css_selector + " > "+ selector})
        #     self.browser.close()# 关闭当前标签页
        sorted(self.form_list, key=operator.itemgetter('len'), reverse=True)
        # 按照表单内容大小排列
        return True

    def handleSpecialPageBefore(self):
        if self.url.find("search.mnr.gov.cn/was/search") >= 0:
            td = self.soup.findAll("td")  # 找页面中所有的td标签
            # for i in td:
            #     if i["attrs"]["height"] == 307:
            td[28].wrap(self.soup.new_tag("form"))  # 将指定标签把当前标签包裹起来
            # break
            pass

    # 建议换成一块一块的显示
    def __get_form_pic(self):
        im = Image.open(self.output_folder + "/screenshot.png")
        for i in range(len(self.form_list)):
            t = self.form_list[i]["form"]
            if self.form_list[i]["type"] == 1: # 如果是iframe中的form
                iframe = self.form_list[i]["css_selector"].split(">f>")[0]  # iframe的selector
                iframe_rect = self.browser.execute_script('return document.querySelector("' + iframe + '").getBoundingClientRect()')
                position_slot = {"left": iframe_rect["left"], "top": iframe_rect["top"]}  # 位置偏移量
                css_selector = self.form_list[i]["css_selector"].split(">f>")[1]  # 表格在iframe中的selector
                slot = 'return document.querySelector("' + iframe + '").contentWindow.'
            else:
                css_selector = self.form_list[i]["css_selector"]
                position_slot = {"left": 0, "top": 0}  # 位置偏移量
                slot = "return "
            t["rect"] = self.browser.execute_script(
                slot + 'document.querySelector("' + css_selector + '").getBoundingClientRect()')
            if float(t["rect"]["width"]) > 10 and float(t["rect"]["height"]) == 0.0:
                # 说明没有被撑开,设置属性使其撑开
                self.browser.execute_script(
                    slot + 'document.querySelector("' + css_selector + '").setAttribute("style", "display:inline-block!important")')
                t["rect"] = self.browser.execute_script(
                    slot + 'document.querySelector("' + css_selector + '").getBoundingClientRect()')  # 重新得到属性
            im2 = Image.new("RGBA", (im.size[0], im.size[1]))
            draw = ImageDraw.Draw(im2)
            rect = t["rect"]
            draw.rectangle([(rect["left"] + position_slot["left"], rect["top"] + position_slot["top"]),
                            (rect["right"] + position_slot["left"], rect["bottom"] + position_slot["top"])],
                           fill=(0, 0, 255, 64))  # 块所在位置的框
            font = ImageFont.truetype("HEI.ttf", size=30,
                                      encoding="unic")  # 设置字体,注意linux里如果没有字体需要指定/usr/share/fonts/HEI.ttf
            if len(self.form_list) - i < 10:  # 数字阴影长度
                l = 20
            else:
                l = 40
            draw.rectangle([(rect["left"] + position_slot["left"], rect["top"] + position_slot["top"]),
                            (rect["left"] + l + position_slot["left"], rect["top"] + 40 + position_slot["top"])],
                           fill=(0, 0, 255, 128))  # 最后一位是透明度，这是字体所属位置的框
            draw.text((rect["left"] + 1 + position_slot["left"], rect["top"] + position_slot["top"]), str(i + 1),
                      font=font)
            for j in range(len(self.form_list[i]["input_list"])):  # 对form中的所有input画框
                if self.form_list[i]["input_list"][j]["form_type"] == 1:
                    css_selector = self.form_list[i]["input_list"][j]["css_selector"].split(">f>")[1]  # 得到css选择器
                else:
                    css_selector = self.form_list[i]["input_list"][j]["css_selector"]  # 得到css选择器
                rect = self.browser.execute_script(
                    slot + 'document.querySelector("' + css_selector + '").getBoundingClientRect()')
                draw.rectangle([(rect["left"] + position_slot["left"], rect["top"] + position_slot["top"]),
                                (rect["right"] + position_slot["left"], rect["bottom"] + position_slot["top"])],
                               fill=(255, 255, 1, 64),
                               outline='black')  # 块所在位置的框
                font = ImageFont.truetype("HEI.ttf", size=15,
                                          encoding="unic")
                draw.rectangle([(rect["left"] + position_slot["left"], rect["top"] + 1 + position_slot["top"]),
                                (rect["left"] + 23 + position_slot["left"], rect["top"] + 20 + position_slot["top"])],
                               fill=(255, 255, 1, 128))  # 最后一位是透明度，这是字体所属位置的框
                draw.text((rect["left"] + 1 + position_slot["left"], rect["top"] + position_slot["top"]),
                          self.form_list[i]["input_list"][j]["index"], font=font,
                          fill=(0, 0, 0, 255))
            for j in range(len(self.form_list[i]["submit_button_list"])):  # 对form中的所有button画框
                if self.form_list[i]["submit_button_list"][j]["form_type"] == 1:
                    css_selector = self.form_list[i]["submit_button_list"][j]["css_selector"].split(">f>")[
                        1]  # 得到css选择器
                else:
                    css_selector = self.form_list[i]["submit_button_list"][j]["css_selector"]  # 得到css选择器
                # ----- 针对特定页面包装 -----
                # if self.url.find("search.mnr.gov.cn/was/search")>=0 and self.form_list[i]["submit_button_list"][j]["type"] == "a":
                #     self.browser.execute_script(
                #         'document.querySelector("' + css_selector + '").setAttribute("style", "display:inline-block!important")')
                # -------------
                rect = self.browser.execute_script(
                    slot + 'document.querySelector("' + css_selector + '").getBoundingClientRect()')
                draw.rectangle([(rect["left"] + position_slot["left"], rect["top"] + position_slot["top"]),
                                (rect["right"] + position_slot["left"], rect["bottom"] + position_slot["top"])],
                               fill=(255, 0, 0, 64),
                               outline='black')  # 块所在位置的框
                font = ImageFont.truetype("HEI.ttf", size=20,
                                          encoding="unic")
                draw.rectangle([(rect["left"] - 20 + position_slot["left"], rect["top"] + position_slot["top"]),
                                (rect["left"] + position_slot["left"], rect["top"] + 25 + position_slot["top"])],
                               fill=(255, 0, 0, 128))  # 最后一位是透明度，这是字体所属位置的框
                draw.text((rect["left"] - 19 + position_slot["left"], rect["top"] + position_slot["top"]),
                          self.form_list[i]["submit_button_list"][j]["index"],
                          font=font)
            im = Image.alpha_composite(im, im2)
        im.save(self.output_folder + "/form_seg_shot.png")

    def __save_form_rules(self):
        form_list = {"url": self.url, "form_check": 0, "main_form_index": 0,"form_exp_link":setting.SERVER_ADDRESS + self.output_folder.replace("static","statics") + "/form_exp.json","forms": self.form_list_json}
        common.save_json(self.output_folder + "/form_list.json", form_list, encoding=setting.OUTPUT_JSON_ENCODING)
        static_exp = {"time": {}}
        static_exp["document_size"] = self.document_size
        static_exp["document_tree_length"] = self.document_tree_length
        static_exp["form_list_lines"] = len(
            open(self.output_folder + "/form_list.json", 'r', encoding='utf-8').readlines())
        static_exp["time"][self.time_crawl.name] = self.time_crawl.getInterval()
        static_exp["time"][self.time_find_form_and_generate_rules.name] = self.time_find_form_and_generate_rules.getInterval()
        common.save_json(self.output_folder + "/form_exp.json", static_exp,
                         encoding=setting.OUTPUT_JSON_ENCODING)

    def __get_element(self, node):
        # for XPATH we have to count only for nodes with same type!
        length = 1
        for previous_node in list(node.previous_siblings):  # 查找本node有多少个兄弟节点
            if isinstance(previous_node, bs4.element.Tag):
                length += 1
        if length > 1:
            return '%s:nth-child(%s)' % (node.name, length)  # 返回css selector
        else:
            return node.name

    def __get_css_selector(self, node,parents=0):
        if parents>0:
            path = []
        else:
            path = [self.__get_element(node)]
        i = 0
        # print(path)
        for parent in node.parents:
            i = i + 1
            if parent.name == "[document]":
                break
            if i > parents:
                path.insert(0, self.__get_element(parent))
            # print(path)
        return ' > '.join(path)  # 一路拼接即得到了css selector

    def remove_slash(self, path):
        for i in range(len(path)):
            if path.endswith('/'):
                path = path[:-1]
            if path.endswith('\\'):
                path = path[:-1]
        return path
