#!/usr/bin/env python
# -*- coding: utf-8 -*-
import operator
import time

import os
from typeAnalyse import typeAnalyse
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from html.parser import HTMLParser
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PIL import Image, ImageDraw, ImageFont
from lcypytools import common
import bs4
from pyquery import PyQuery as pq
from lcypytools.common import Timer

import requests
import shutil
import setting


# 根据html源码和rank得到text文本
def get_text_from_rank(htm, rank):
    i = 0
    htm = BeautifulSoup(htm, 'html.parser')  # html转换成rank
    for text in htm.stripped_strings:  # 当一个Tag对象有多个子节点时，可以用.strings方法再通过遍历获得所有子节点的内容。
        if i == rank:
            return text
        i += 1


# Selenium-WebDriverApi接口详解 - 尘世风 - 博客园
# https://www.cnblogs.com/feng0815/p/8334144.html
"""
这里会把同一级的元素全都算进去，就算他们结构不同
因为，级别用lid表示，每一层都独一无二，所以错误率很低！！
"""


class Segment:
    def __init__(self, log, form_check=0, form_path="form_list.json"):
        options = Options()
        options.binary_location = setting.CHROME_BINARY_LOCATION
        options.add_argument('--headless')  # 不显示浏览器
        self.browser = webdriver.Chrome(chrome_options=options, executable_path=setting.DRIVER_PATH)
        self.browser.set_window_size(setting.SCREEN_WIDTH, 800)  # set the window size that you need
        self.parser = HTMLParser()
        self.log = log
        self.form_check = form_check
        self.form_path = form_path

    def segment(self, url, output_folder="output", is_output_images=False):
        self.url = url
        self.output_folder = self.remove_slash(output_folder)  # 去除冗余信息后得到的路径
        """
        爬取表单页面时间、查找表单时间、处理动态表单输入内容时间、
        网页分块时间、生成并对网页主题块进行排序的时间、生成最终规则文档的时间
        """
        self.time_crawl = Timer("crwal_static_page")
        self.log.write("Crawl HTML Document from %s,please wait for about 40s(max 60s)" % self.url)
        self.__crawler()  # 爬取页面
        self.time_crawl.end()

        self.time_form_handle = Timer("input_forms_handle")
        self.log.write("Handling the input forms on %s" % self.url)
        self.__read_form_rules_and_type()  # 爬取页面
        self.time_form_handle.end()

        self.time_web_segmentation = Timer("web_segmentation")
        self.log.write("Run Pruning on %s" % self.url)
        self.__pruning()  # 得到广度优先搜索列表
        self.log.write("Run Partial Tree Matching on %s" % self.url)
        self.__partial_tree_matching()
        self.log.write("Run Backtracking on %s" % self.url)
        self.__backtracking()
        self.log.write("Merging and generating rules and blocks on %s,process:0%%" % (self.url))
        self.__output()
        self.time_web_segmentation.end()

        self.time_web_seg_sort = Timer("web_seg_sort")
        self.log.write("Selecting the main segment on %s" % self.url)
        self.__select_main_segment_top_min()
        self.log.write("Generating sections on %s" % self.url)
        self.__generate_sections()
        self.time_web_seg_sort.end()

        self.time_generate_documents = Timer("generate_documents")
        self.log.write("Generating api_info on  %s" % self.url)
        self.__generate_api_info()
        self.log.write("Generating rules on  %s" % self.url)
        self.__generate_rules()
        self.time_generate_documents.end()
        self.log.write("Output Result JSON File on  %s" % self.url)
        self.__save()

        if is_output_images:
            self.log.write("Output Images on  %s" % self.url)
            self.__output_images()

        self.log.write("Finished on  %s" % self.url)
        self.log.write_without_datetime(
            "200 " + setting.SERVER_ADDRESS + self.output_folder.replace("static", "statics") + "/api_info.json")

    def __crawler(self):
        self.browser.set_page_load_timeout(60)  # 最长等待时间
        try:
            time_start = time.time()
            self.browser.get(self.url)
            self.document_size = len(self.browser.page_source)
            self.document_tree_length = self.browser.execute_script("return document.getElementsByTagName('*').length")
            time_end = time.time()
            self.interval = time_end - time_start  # 记录第一次打开页面需要多长时间，下次就等待多长时间
            time.sleep(3)  # 强行等待3s
        except TimeoutException:
            self.log.write_without_datetime("503 " + "request time out,task end,please retry")
            self.browser.quit()
            exit(-1)
        self.page = pq(self.browser.page_source.replace('xmlns', 'another_attr'))  # pyquery
        self.th_num = self.page("th").length
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
        ######

    """
    通过下面的操作，程序得到了整个网页中所有的tag节点的信息，并按照广度优先搜索的顺序，存储到了self.allnodes列表中
    去除了类似注释，js，css等无用信息，以及空格和空行。
    同时，因为使用了beautiful soup，因此网页信息会自动容错。
    """

    def __pruning(self):
        # 处理特定页面
        if self.url.find("http://www.dsac.cn") >= 0:
            self.soup = self.soup.find("div", class_="mainBar_body")
            tagbody = self.soup
        else:
            tagbody = self.soup.find("body")  # 得到body体
        tagbody["lid"] = str(-1)
        tagbody["sn"] = str(1)  # <body lid="-1" sn="1".../>
        tagbody["ttype"] = 0  # 是否为iframe中的标签
        tagbody["parent_path"] = ""
        self.allnodes = [tagbody]  # put body block into allnodes list
        i = 0
        while len(self.allnodes) > i:
            children = []
            # ----以下内容针对iframe进行-----
            iframe_soup = []
            css_selector = ""
            if self.allnodes[i].name == "iframe":
                css_selector = self.__get_css_selector(self.allnodes[i])
                try:
                    self.browser.switch_to.frame(self.browser.find_element_by_css_selector(css_selector))  # 切换到此iframe
                    iframe_soup = BeautifulSoup(self.browser.page_source)
                    self.browser.switch_to.default_content()  # 切换到默认页面
                except:
                    pass  # 有些iframe可能为空，跳过
            if len(iframe_soup) > 0:
                for child in iframe_soup.children:
                    if isinstance(child, bs4.element.Tag):  # 如果直接子节点是TAG类型，则放入children列表，即得到正文中的所有显示出的信息（去除注释及其他代码）
                        child["ttype"] = 1  # 标记为iframe中的元素
                        child["parent_path"] = css_selector + " >f> "
                        children.append(child)
            # ------------------

            for child in self.allnodes[i].children:
                if isinstance(child, bs4.element.Tag):  # 如果直接子节点是TAG类型，则放入children列表，即得到正文中的所有显示出的信息（去除注释及其他代码）
                    children.append(child)
            sn = len(children)

            for child in children:
                child["lid"] = str(i)  # 广度优先搜索顺序
                child["sn"] = str(sn)  # 本层节点数目
                if self.allnodes[i]["ttype"] == 1:
                    child["ttype"] = 1
                    child["parent_path"] = self.allnodes[i]["parent_path"]
                elif self.allnodes[i].name != "iframe":  # 标记为iframe中的元素
                    child["ttype"] = 0
                    child["parent_path"] = ""
                # 注意，这里一旦修改了节点属性，则数组里所有包含此节点的属性都会被修改！！！！！
                self.allnodes.append(child)  # 加入allnodes节点
            i += 1
        pass

    def __partial_tree_matching(self):
        self.blocks = []
        lid_old = -2
        i = 0
        while i < len(self.allnodes):  # 广度优先遍历
            node = self.allnodes[i]
            if 'extracted' in node.attrs:  # 已经提取过的不再次提取
                i += 1
                continue
            sn, lid = int(node["sn"]), int(node["lid"])
            if lid != lid_old:  # 每次换了层数
                max_window_size = int(sn / 2)  # 重新计算窗口大小
                lid_old = lid
            """
            这里遍历的时候，以窗口为大小进行遍历
            两层for循环，第一层控制窗口大小分别为1到max_window_size
            第二层根据窗口大小，划分块大小为1,2等，如块大小为2，则pew是第i个节点的前两个兄弟节点；cew为i和i+1的节点；new为i+2和i+3
            然后对三个数组进行比较
            
            这里的算法解释：从窗口为1开始到窗口大小为sn/2结束，如1，2，3，分别试验1个node，2个node等结合在一起之后的结构
            是不是相同的，如果是，就break这个节点，标记好；不然就看两个，3个直到结束找到可能相同的结构。
            
            """
            for ws in range(1, max_window_size + 1):  # body则什么都不做
                pew, cew, new = [], [], []  # 应该是在找当前节点和当前节点的上下兄弟节点
                for wi in range(i - ws, i + 2 * ws):
                    if wi >= 0 and wi < len(self.allnodes) and int(self.allnodes[wi]["lid"]) == lid:  # 要判定block处于同一层
                        cnode = self.allnodes[wi]
                        if wi >= i - ws and wi < i:
                            pew.append(cnode)
                        if wi >= i and wi < i + ws:
                            cew.append(cnode)
                        if wi >= i + ws and wi < i + 2 * ws:
                            new.append(cnode)
                        pass
                isle = self.__compare_nodes(pew, cew)
                isre = self.__compare_nodes(cew, new)
                if isle or isre:
                    self.blocks.append(cew)  # block里加入的是一个大块数组，数组里的所有元素为一个整体
                    i += ws - 1  # 如果被标记成了一个block，则下一个node无需遍历，因为下下行已经标记过了
                    max_window_size = len(cew)  # 窗口大小变为当前窗口大小，即如果已经确定如2个结合在一起是一个块的话，下一个节点就不需要再分析到2以上了。
                    self.__mark_extracted(cew)  # 将这个块内的元素标记为已经提取过的块
                    break
            i += 1
        pass

    def __mark_extracted(self, nodes):
        for node in nodes:  # 对数组里所有的node，标记为extracted
            node["extracted"] = ""
            lid = node["lid"]
            parent = node
            while parent.parent is not None:
                parent = parent.parent
                parent["extracted"] = ""  # 此节点所有的祖先节点标记为已遍历
                parent["sid"] = lid  # 此节点所有的祖先节点增加新属性sid为此节点层数

            nodecols = [node]
            for nodecol in nodecols:  # 对此节点的所有后代节点标记为已遍历
                for child in nodecol.children:
                    if isinstance(child, bs4.element.Tag):
                        nodecols.append(child)
                nodecol["extracted"] = ""  # 所有后代节点全部标记为已标记，同时会影响数组里的全部含有此node的值，即相同结构的块越大越好！！！！

    def __compare_nodes(self, nodes1, nodes2):
        if len(nodes1) == 0 or len(nodes2) == 0:
            return False

        return self.__get_nodes_children_structure(nodes1) == self.__get_nodes_children_structure(nodes2)
        pass

    def __get_nodes_children_structure(self, nodes):
        structure = ""  # 如果有多个node拼接，则简单将每个节点的结构进行加和即可
        for node in nodes:
            structure += self.__get_node_children_structure(node)
        # print(nodes,structure)
        # spanspaniullilispan  类似这种,广度优先！！
        """
        [<input class="bul2 fl" id="header-srch" lid="23" maxlength="50" placeholder="输入关键词搜索" sn="6" style="height:15px;border:3px solid #002A56;background-color:#fff" type="text" value=""/>, <span class="header-srch-type db dn c_999" data-header-type="" lid="23" sn="6"><span lid="34" sn="2">服务</span><i class="ml5 caret caret-down caret-b-9b" lid="34" sn="2"></i></span>, <ul class="new-header-dropdown-list header-srch-type-list dn" data-header-type-list="" lid="23" sn="6">
<li class="header-dropdown-item tc cur-hand active" lid="35" sn="2">服务</li>
<li class="header-dropdown-item tc cur-hand " lid="35" sn="2">服务商</li>
</ul>] inputspanspaniullili
        """
        # print(structure)
        return structure

    def __get_node_children_structure(self, node):
        nodes = [node]
        structure = ""
        for node in nodes:
            for child in node.children:
                if isinstance(child, bs4.element.Tag):
                    # and (node.name != "td" and node.name!="th") 广度优先遍历元素的child，但是显式忽略td内部的结构，已证明不合适
                    nodes.append(child)
            if node.name != "tbody" and node.name != "thead":  # 跳过两个标签
                if node.name == "th":  # th换成td,不能直接改变node.name的值，因为beautifulsoup是联动修改的！！
                    structure += "td"
                    # break # 试着写 到了td就停止 不管里面的结构是什么样子
                else:
                    structure += node.name  # 结构即节点名字，调试看下
        # print(structure)
        return structure

    # 找到文字所在标签并根据属性返回相应值
    def __get_tag_attr(self, css_selector, text):
        try:
            # css_selector.split(">f>")[1]
            if css_selector.find(">f>")>=0: # 对iframe中元素的特殊处理
                self.browser.switch_to.frame(self.browser.find_element_by_css_selector(css_selector.split(">f>")[0]))
                node = BeautifulSoup(pq(self.browser.page_source.replace('xmlns', 'another_attr'))(css_selector.split(">f>")[1]).html())
                self.browser.switch_to.default_content()
            else:
                node = BeautifulSoup(self.page(css_selector).html())
            nodes = [node]
            for node in nodes:
                for child in node.children:
                    if isinstance(child, bs4.element.Tag):
                        nodes.append(child)
                        if child.text.strip() == text:  # 注意去除空格
                            text = ""
                            if "id" in child.attrs:
                                text = child.attrs["id"]
                            elif "name" in child.attrs:
                                text = child.attrs["name"]
                            # elif "alt" in child.attrs:
                            #     text = child.attrs["alt"]
                            # elif "title" in child.attrs:
                            #     text = child.attrs["title"]
                            elif "class" in child.attrs:
                                text = " ".join(child.attrs["class"])
                            return text
        except:
            pass
        return ""

    """
    对于第一轮遍历没有标记为任何块的节点，找到最大的node，即最粗的块，当做一块加入block
    """

    def __backtracking(self):
        for node in self.allnodes:
            if (node.name != "body") and (node.parent is not None) and ('extracted' not in node.attrs) and (
                    'extracted' in node.parent.attrs):
                self.blocks.append([node])
                self.__mark_extracted([node])

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

    def __get_css_selector(self, node):
        path = [self.__get_element(node)]
        try:
            t = node["parent_path"]
        except:
            t = ""
        for parent in node.parents:
            if parent.name == "[document]":
                break
            path.insert(0, self.__get_element(parent))
        return t + ' > '.join(path)  # 一路拼接即得到了css selector

    def __get_css_background_image_urls(self, node):  # 得到此节点下所有的img图像
        nodes = [node]
        nodes_output = []
        image_urls = []
        structure = ""
        for node in nodes:  # 广度优先的node所有子孙节点数组
            for child in node.children:
                if isinstance(child, bs4.element.Tag):
                    nodes.append(child)
        for node in nodes:
            try:
                css_selector = self.__get_css_selector(node)  # 得到css选择器
                url = self.browser.find_element_by_css_selector(css_selector).value_of_css_property(
                    "background-image")  # 得到此属性
                if url != "none":
                    nodes_output.append(node)  # 存在背景图片的node添加进来
                    url = url.replace('url(', '').replace(')', '').replace('\'', '').replace('\"', '')
                    url = urljoin(self.url, url)
                    image_urls.append(url)
            except:
                pass
        return image_urls, nodes_output

    def __rgba2RGBA(self, rgba):
        try:
            rgba = rgba.replace("rgba(", "").replace(")", "")
            (R, G, B, A) = tuple(rgba.split(","))
            return int(R), int(G), int(B), float(A)
        except:
            return 0, 0, 0, 0

    def __get_css_background_color(self, node):
        nodes = [node]
        for p in node.parents:
            nodes.append(p)

        (R, G, B) = (255, 255, 255)
        for node in nodes:
            try:
                css_selector = self.__get_css_selector(node)
                color = self.browser.find_element_by_css_selector(css_selector).value_of_css_property(
                    "background-color")

                Rn, Gn, Bn, A = self.__rgba2RGBA(color)

                if A == 1:
                    (R, G, B) = (Rn, Gn, Bn)
                    break
            except:
                pass
        return R, G, B

    """
    这里加上每一个元素的css selector，包括text和img，以及对应含义！！！！
    把a的text和link合并起来！！
    """

    def __output(self):
        segids = []
        rid = 0
        segs = dict()
        num = len(self.blocks)
        for i, block in enumerate(self.blocks):
            self.log.write(
                "Merging and generating rules and blocks on %s，process:%.0f%%" % (self.url, float(i * 100 / num)))
            # textsnode
            texts, images, links, cssselectors, linktexts, linktextsindexes, nodes_img_total = [], [], [], [], [], [], []
            for node in block:
                # print(node.name)
                # extract hyperlink from node
                link_index = -1
                for link in node.find_all("a"):
                    link_index += 1
                    if "href" in link.attrs:
                        textlist, imglist = [], []
                        rank = 0
                        for text in link.stripped_strings:  # 当一个Tag对象有多个子节点时，可以用.strings方法再通过遍历获得所有子节点的内容。
                            linktexts.append(text)
                            linktextsindexes.append(link_index)
                            textlist.append({"text": text, "css_selector": self.__get_css_selector(link), "rank": rank})
                            rank += 1
                        # extract images in css background
                        background_image_urls, nodes_img = self.__get_css_background_image_urls(link)
                        nodes_img_total.append(nodes_img)
                        k = 0
                        for url in background_image_urls:  # 对img的处理方式
                            dict_img = dict()
                            # dict_img["alt"] = ""
                            dict_img["type"] = "background_img"
                            dict_img["src"] = urljoin(self.url, url)
                            dict_img["css_selector"] = self.__get_css_selector(nodes_img[k])  # 得到css_selector
                            r, g, b = self.__get_css_background_color(nodes_img[k])
                            dict_img["bg_color"] = "%d,%d,%d" % (r, g, b)
                            imglist.append(dict_img)
                            k += 1
                        # extract images in css background
                        # -- end

                        # extract images in <img> element
                        for img in link.find_all("img"):
                            nodes_img_total.append(img)
                            dict_img = dict()
                            if "src" in img.attrs:
                                dict_img["src"] = urljoin(self.url, img["src"])
                            if "alt" in img.attrs:
                                dict_img["alt"] = img["alt"]
                            if "title" in img.attrs:
                                dict_img["title"] = img["title"]
                            dict_img["type"] = "img"
                            dict_img["css_selector"] = self.__get_css_selector(img)  # 得到css_selector
                            imglist.append(dict_img)
                            r, g, b = self.__get_css_background_color(img)
                            dict_img["bg_color"] = "%d,%d,%d" % (r, g, b)
                        links.append({"href": urljoin(self.url, link["href"]), "texts": textlist, "images": imglist,
                                      "css_selector": self.__get_css_selector(link)})
                # extract hyperlink from node -- end

                # extract images in css background
                background_image_urls, nodes_img = self.__get_css_background_image_urls(node)
                k = 0
                for url in background_image_urls:  # 对img的处理方式
                    if nodes_img[k] not in nodes_img_total:
                        dict_img = dict()
                        dict_img["type"] = "background_img"
                        dict_img["src"] = urljoin(self.url, url)
                        dict_img["css_selector"] = self.__get_css_selector(nodes_img[k])  # 得到css_selector
                        r, g, b = self.__get_css_background_color(nodes_img[k])
                        dict_img["bg_color"] = "%d,%d,%d" % (r, g, b)
                        images.append(dict_img)
                        k += 1
                # extract images in css background
                # -- end

                # extract images in <img> element
                for img in node.find_all("img"):
                    if img not in nodes_img_total:
                        dict_img = dict()
                        if "src" in img.attrs:
                            dict_img["src"] = urljoin(self.url, img["src"])
                        if "alt" in img.attrs:
                            dict_img["alt"] = img["alt"]
                        if "title" in img.attrs:
                            dict_img["title"] = img["title"]
                        dict_img["type"] = "img"
                        dict_img["css_selector"] = self.__get_css_selector(img)  # 得到css_selector
                        images.append(dict_img)
                        r, g, b = self.__get_css_background_color(img)
                        dict_img["bg_color"] = "%d,%d,%d" % (r, g, b)
                # extract images in <img> element
                # 这里可以加个button或者input！！！！

                # extract text from node
                rank = 0
                link_index = 0
                index_before = -1  # 记录上面的index是否有变化，从0计数
                index_inner = 0
                for text in node.stripped_strings:  # 当一个Tag对象有多个子节点时，可以用.strings方法再通过遍历获得所有子节点的内容。
                    # print(text,self.__get_css_selector(node),linktexts)

                    # texts_for_th.append(text) # 为th表头专门设置一个数组来存储
                    # if text not in linktexts :  # 单独处理链接项,这种处理方法带来的问题是，当有的非链接文字和链接文字相同时，会发生冲突，少了很多内容
                    if text not in linktexts:
                        texts.append({"text": text, "css_selector": self.__get_css_selector(node), "rank": rank})
                    else:  # 标记此link的text在所在大块所处的位置
                        try:
                            if index_before != linktextsindexes[link_index]:  # 换了一个新的link时
                                index_before = linktextsindexes[link_index]
                                index_inner = 0  # 从0开始计数
                            # print(link_index,index_inner)
                            links[linktextsindexes[link_index]]["texts"][index_inner]["node_rank"] = rank
                            link_index += 1
                            index_inner += 1
                        except:
                            pass  # 当有的非链接文字和链接文字相同时，会发生冲突，少了很多内容，忽略掉，例子：http://cspo.zju.edu.cn/search.php?postflag=1&area=712591&kw_qbzc=%C7%EB%CA%E4%C8%EB%B9%D8%BC%FC%B4%CA#
                    rank += 1
                # extract text from node -- end
                cssselectors.append(self.__get_css_selector(node))

            if len(texts) == 0 and len(images) == 0 and len(links) == 0:
                continue

            lid = block[0]["lid"]
            if lid not in segids:
                segids.append(lid)
            sid = str(segids.index(lid))  # ！！！核心在这，将同一层的lid相同的内容放在一起！lid的值是上面函数定义好的# ！！

            if sid not in segs:
                segs[sid] = {"segment_id": int(sid), "css_selector": self.__get_css_selector(block[0].parent),
                             "records": []}

            segs[sid]["records"].append(
                {"record_id": rid, "texts": texts, "images": images, "css_selector": cssselectors, "links": links})
            print(cssselectors)
            rid += 1

        self.json_data = dict()
        self.json_data["segments"] = [value for key, value in segs.items()]  # 注意这里是个dict,
        self.json_data["url"] = self.url
        self.json_data["title"] = self.browser.title

    # 找到主要至多min2个的section
    def __select_main_segment_top_min(self, min2=10):
        segments = self.json_data["segments"]
        self.main_sec = None
        max_len = 0
        max_str = 0
        array, array2 = [], []
        i = 0
        for seg in segments:
            records = seg["records"]
            # print(len(records),len(str(records)))
            # 如果列表项目和长度都比之前的大，替换;
            # 如果列表长度比之前的1.5倍都大，替换；
            if (len(records) >= max_len and len(str(records)) > max_str * 1.2) or len(records) >= max_len * 1.5:
                max_len = len(records)
                max_str = len(str(records))
                self.main_sec = seg
                self.main_sec_id = i
            array.append({"seg": seg, "len": len(records), "id": i})
            array2.append({"seg": seg, "len_str": len(str(records)), "id": i})
            i += 1
        sorted_len_array = sorted(array, key=operator.itemgetter('len'), reverse=True)
        sorted_len_str = sorted(array2, key=operator.itemgetter('len_str'), reverse=True)
        index = min(min2, len(array))
        sorted_len_array = sorted_len_array[:index]
        sorted_len_str = sorted_len_str[:index]
        sorted_len_array.extend(sorted_len_str)
        choice = set()
        for id in sorted_len_array:
            choice.add(id["id"])
        choice = list(choice)
        candidate = []
        for id in choice:
            t = array[id]  # 认为条数最多的是最大块
            css_selector = t["seg"]["css_selector"]
            if css_selector.find(">f>") >= 0:  # 处理iframe
                iframe = css_selector.split(">f>")[0]
                slot = 'return document.querySelector("' + iframe + '").contentWindow.'
                iframe_rect = self.browser.execute_script(
                    'return document.querySelector("' + iframe + '").getBoundingClientRect()')
                position_slot = {"left": iframe_rect["left"], "top": iframe_rect["top"]}  # 位置偏移量
                css_selector = css_selector.split(">f>")[1]
                self.browser.switch_to.frame(self.browser.find_element_by_css_selector(iframe))  # 切换到此iframe
                t["content"] = self.browser.find_element_by_css_selector(css_selector).text
                self.browser.switch_to.default_content()  # 切换到默认页面
            else:
                t["content"] = self.browser.find_element_by_css_selector(css_selector).text
                position_slot = {"left": 0, "top": 0}  # 位置偏移量
                slot = "return "

            t["rect"] = self.browser.execute_script(
                slot + 'document.querySelector("' + css_selector + '").getBoundingClientRect()')
            t["rect"]["left"] += position_slot["left"] # iframe中的位置相对标准位置有偏移
            t["rect"]["top"] += position_slot["top"]
            t["rect"]["right"] += position_slot["left"] # iframe中的位置相对标准位置有偏移,不要忘了这两句！
            t["rect"]["bottom"] += position_slot["top"]
            # t["len"] = float(t["rect"]["width"]) * float(t["rect"]["height"]) # 按照面积排序不太好的地方在于划分快的时候有些块有重叠，不一定面积最大的块就最好，反例：李克强！！！！
            if float(t["rect"]["width"]) > 10:  # 如果宽度>10，即可显示才加入分割区域，这里不能使用面积，因为会出现有weight但是没有height(即没有被撑开的情况）
                if float(t["rect"]["width"]) > 10 and float(t["rect"]["height"]) == 0.0:  # 说明没有被撑开,设置属性使其撑开
                    self.browser.execute_script(
                        slot + 'document.querySelector("' + css_selector + '").setAttribute("style", "display:inline-block!important")')
                    t["rect"] = self.browser.execute_script(
                        slot + 'document.querySelector("' + css_selector + '").getBoundingClientRect()')  # 重新得到属性
                candidate.append(t)
        candidate = sorted(candidate, key=operator.itemgetter("len"), reverse=True)
        index = min(min2, len(candidate))
        self.candidate = candidate[:index]  # 选出的sections,最多8个
        # print("main:",self.main_sec)
        #
        # self.element = {"content": self.browser.execute_script(
        #     'return document.querySelector("' + self.main_sec["css_selector"] + '")').text}  # 存储主要信息
        # # 下面几行对mainsection进行截图
        # rect = self.browser.execute_script('return document.querySelector("' + self.main_sec[
        #     "css_selector"] + '").getBoundingClientRect()')  # 在页面上执行js代码，并获得main_segment的位置和大小
        # im = Image.open(self.output_folder + "/screenshot.png")
        # im = im.crop((
        #     max(0, rect["left"] - 10), max(0, rect["top"] - 10), min(rect["right"] + 10, setting.SCREEN_WIDTH),
        #     min(rect["bottom"] + 10, self.page_height)))  # 前端用滚动条显示图片！！！
        # # im = im.crop((rect["left"], rect["top"],rect["right"],rect["bottom"]))  # 前端用滚动条显示图片！！！
        # im.save(self.output_folder + "/sec_shot.png")

    def __generate_sections(self):
        im = Image.open(self.output_folder + "/screenshot.png")
        for i in range(len(self.candidate)):
            t = self.candidate[len(self.candidate) - i - 1]
            im2 = Image.new("RGBA", (im.size[0], im.size[1]))
            draw = ImageDraw.Draw(im2)
            rect = t["rect"]
            draw.rectangle([(rect["left"], rect["top"]), (rect["right"], rect["bottom"])],
                           fill=(0, 0, 255, 64))  # 块所在位置的框
            font = ImageFont.truetype("HEI.ttf", size=30,
                                      encoding="unic")  # 设置字体,注意linux里如果没有字体需要指定/usr/share/fonts/HEI.ttf
            if len(self.candidate) - i < 10:  # 数字阴影长度
                l = 20
            else:
                l = 40
            draw.rectangle([(rect["left"], rect["top"]), (rect["left"] + l, rect["top"] + 40)],
                           fill=(0, 0, 255, 128))  # 最后一位是透明度，这是字体所属位置的框
            draw.text((rect["left"] + 1, rect["top"]), str(len(self.candidate) - i), font=font)
            im = Image.alpha_composite(im, im2)
        im.save(self.output_folder + "/seg_shot.png")

    def __generate_api_info(self):
        self.api_info = dict()
        self.api_info["api_name"] = self.browser.title
        if self.form_path != "form_list.json":
            self.api_info["form_rules_link"] = setting.SERVER_ADDRESS + self.form_path.replace("static", "statics")
        else:
            self.api_info["form_rules_link"] = setting.SERVER_ADDRESS + "statics/form_list.json"
        ## 换成description
        try:
            description = self.soup.find(attrs={"name": "description"})['content']  # 存在description就用，不然就用title
        except:
            description = self.browser.title
        self.api_info["api_description"] = description
        self.api_info["api_url"] = self.url
        self.api_info["img_link"] = setting.SERVER_ADDRESS + self.output_folder + "/seg_shot.png"
        # self.api_info["img_seg_link"] = setting.SERVER_ADDRESS + self.output_folder + "/seg_shot.png"
        self.api_info["api_crawl_rules_link"] = setting.SERVER_ADDRESS + self.output_folder.replace("static",
                                                                                                    "statics") + "/rules_list.json"
        self.api_info["json_link"] = setting.SERVER_ADDRESS + self.output_folder.replace("static",
                                                                                         "statics") + "/example.json"
        self.api_info["static_exp_link"] = setting.SERVER_ADDRESS + self.output_folder.replace("static",
                                                                                         "statics") + "/static_exp.json"
        self.api_info["main_sec_id"] = [0]  # 默认主题块位置
        self.api_info["sections"] = []
        self.api_info["candidate"] = []
        sid = 0
        for c in self.candidate:
            sid = sid + 1
            self.api_info["sections"].append(c["content"])
            format_list = {"section_name":"section_"+ str(sid),"items":[]}
            if len(c["seg"]["records"]) > 0:
                id = 0
                info = c["seg"]["records"][0]  # 取第1个元素，下面写判断th的数组情况
                if self.th_num > 0 and info["css_selector"][0].find("table") >= 0:
                    th = dict()
                    th_selector = info["css_selector"][0].replace("tr:nth-child(2)",
                                                                  "tr:nth-child(1)")  # 如果默认是第二个元素，则替换成第一个元素，即th
                    if th_selector.find(">f>") >= 0:  # 处理iframe
                        iframe = th_selector.split(">f>")[0]
                        slot = 'return document.querySelector("' + iframe + '").contentWindow.'
                        css_selector = th_selector.split(">f>")[1]
                    else:
                        slot = "return "
                        css_selector = th_selector
                    htm = self.browser.execute_script(
                        slot + 'document.querySelector("' + css_selector + '").outerHTML')
                    htm = BeautifulSoup(htm, 'html.parser')  # html转换成rank
                    t = 0
                    for text in htm.stripped_strings:
                        th[str(t)] = text
                        t += 1
                for text in info["texts"]:
                    format = dict()
                    format["id"] = id
                    analyse = typeAnalyse(text['text'],"_S" + str(sid) + "I" + str(id)).getType()
                    # 使用KG工具对文本进行分词并尝试分析字段含义
                    if analyse == "text": # 如果没分析出来字段类型，尝试默认分析方法
                        text_t = self.__get_tag_attr(text["css_selector"], text['text'])
                        if len(text_t) <= 0:
                            format["name"] = "text_" + "S" + str(sid) + "I" + str(id)
                        else:
                            format["name"] = text_t
                    else:
                        format["name"] = analyse
                    if self.th_num > 0 and text["css_selector"].find("table") >= 0:
                        # 如果网页存在th标签且元素在表格内
                        format["name"] = th[str(text['rank'])]  # 填充成上面th的值
                    format["description"] = "text_description"
                    format["type"] = "text"
                    format["example"] = text['text']
                    format["select"] = 1
                    format["parent_id"] = -1  # 直接父元素为-1
                    format_list["items"].append(format)
                    text["id"] = id
                    id += 1
                for image in info["images"]:
                    format = dict()
                    format["id"] = id
                    text_t = ""
                    if image['css_selector'].find(">f>") >= 0:  # 对iframe中元素的特殊处理
                        self.browser.switch_to.frame(
                            self.browser.find_element_by_css_selector(image['css_selector'].split(">f>")[0]))
                        child = pq(self.browser.page_source.replace('xmlns', 'another_attr'))(image['css_selector'].split(">f>")[1])[0].attrib
                        self.browser.switch_to.default_content()
                    else:
                        child = self.page(image['css_selector'])[0].attrib
                    if "id" in child:
                        text_t = child["id"]
                    elif "name" in child:
                        text_t = child["name"]
                    elif "class" in child:
                        text_t = child["class"]
                    if len(text_t) <= 0:
                        format["name"] = "image_" + "S" + str(sid) + "I" + str(id)
                    else:
                        format["name"] = text_t
                    format["description"] = "image_description"
                    format["type"] = "img"
                    exp = "{"
                    if "src" in image:
                        exp += ("src:'" + image["src"] + "',")
                    if "alt" in image:
                        exp += ("alt:'" + image["alt"] + "',")
                    if "title" in image:
                        exp += ("title:'" + image["title"] + "',")
                    if exp.endswith(","):
                        exp = exp[:-1]  # 去除最后一个逗号
                    exp += "}"
                    format["example"] = exp
                    format["select"] = 1
                    format["parent_id"] = -1  # 直接父元素为-1
                    format_list["items"].append(format)
                    image["id"] = id
                    id += 1
                for link in info["links"]:
                    format = dict()
                    format["id"] = id
                    format["parent_id"] = -1
                    format["name"] = "link_" + "S" + str(sid) + "I" + str(id)
                    t = format["name"]
                    tid = format["id"]  # 临时保存linkid
                    format["description"] = "link_description"
                    format["type"] = "link"
                    format["example"] = "{href:'" + link['href'] + "'}"
                    format["select"] = 1
                    format_list["items"].append(format)
                    link["id"] = id
                    id += 1
                    for text in link["texts"]:
                        format = dict()
                        format["id"] = id
                        text["id"] = id
                        analyse = typeAnalyse(text['text'],"_S" + str(sid) + "I" + str(id)).getType()
                        # 使用KG工具对文本进行分词并尝试分析字段含义
                        if analyse == "text":  # 如果没分析出来字段类型，尝试默认分析方法
                            text_t = self.__get_tag_attr(text["css_selector"], text['text'])
                            if len(text_t) <= 0:
                                format["name"] = "text_" + "S" + str(sid) + "I" + str(id)
                            else:
                                format["name"] = "link_text_" + "S" + str(sid) + "I" + str(id)
                        else:
                            format["name"] = analyse
                        if self.th_num > 0 and text["css_selector"].find("table") >= 0:
                            # 如果网页存在th标签且元素在表格内
                            format["name"] = th[str(text['node_rank'])]  # 填充成上面th的值
                        format["description"] = "link_text_description_related_to_" + t
                        format["type"] = "text"
                        format["example"] = text['text']
                        format["select"] = 1
                        format_list["items"].append(format)
                        format["parent_id"] = tid
                        id += 1
                    for image in link["images"]:
                        format = dict()
                        format["id"] = id
                        image["id"] = id
                        text_t = ""
                        if image['css_selector'].find(">f>") >= 0:  # 对iframe中元素的特殊处理
                            self.browser.switch_to.frame(
                                self.browser.find_element_by_css_selector(image['css_selector'].split(">f>")[0]))
                            child = pq(self.browser.page_source.replace('xmlns', 'another_attr'))(
                                image['css_selector'].split(">f>")[1])[0].attrib
                            self.browser.switch_to.default_content()
                        else:
                            child = self.page(image['css_selector'])[0].attrib
                        if "id" in child:
                            text_t = child["id"]
                        elif "name" in child:
                            text_t = child["name"]
                        elif "class" in child:
                            text_t = child["class"]
                        if len(text_t) <= 0:
                            format["name"] = "link_image_" + "S" + str(sid) + "I" + str(id)
                        else:
                            format["name"] = text_t
                        format["description"] = "link_image_description_related_to_" + t
                        format["type"] = "img"
                        exp = "{"
                        if "src" in image:
                            exp += ("src:'" + image["src"] + "',")
                        if "alt" in image:
                            exp += ("alt:'" + image["alt"] + "',")
                        if "title" in image:
                            exp += ("title:'" + image["title"] + "',")
                        if exp.endswith(","):
                            exp = exp[:-1]  # 去除最后一个逗号
                        exp += "}"
                        format["example"] = exp
                        format["select"] = 1
                        format["parent_id"] = tid
                        format_list["items"].append(format)
                        id += 1
            self.api_info["candidate"].append(format_list)

    def __generate_rules(self):
        self.rules_list = []
        for c in self.candidate:
            id = -1
            rules_list = []
            if len(c["seg"]["records"]) > 0:
                first_element = c["seg"]["records"][0]
                for info in c["seg"]["records"]:
                    id += 1
                    rule = dict()
                    rule["record_id"] = id
                    texts = []
                    i = 0
                    for text in info["texts"]:
                        try:
                            texts.append({"id": first_element["texts"][i]["id"], "css_selector": text["css_selector"],
                                          "rank": text["rank"]})
                        except:
                            pass
                        i += 1
                    rule["texts"] = texts
                    images = []
                    i = 0
                    for image in info["images"]:
                        try:
                            images.append(
                                {"id": first_element["images"][i]["id"], "css_selector": image["css_selector"],
                                 "type": image["type"]})
                        except:
                            pass
                        i += 1
                    rule["images"] = images
                    links = []
                    i = 0
                    for link in info["links"]:
                        link_rule = dict()
                        try:
                            link_rule["id"] = first_element["links"][i]["id"]
                            link_rule["css_selector"] = link["css_selector"]
                        except:
                            pass
                        texts = []
                        j = 0
                        for text in link["texts"]:
                            try:
                                texts.append({"id": first_element["links"][i]["texts"][j]["id"],
                                              "css_selector": text["css_selector"],
                                              "rank": text["rank"]})
                            except:
                                pass
                            j += 1
                        link_rule["texts"] = texts
                        images = []
                        j = 0
                        for image in link["images"]:
                            try:
                                images.append({"id": first_element["links"][i]["images"][j]["id"],
                                               "css_selector": image["css_selector"],
                                               "type": image["type"]})
                            except:
                                pass
                            j += 1
                        link_rule["images"] = images
                        links.append(link_rule)
                        i += 1
                    rule["links"] = links
                    rules_list.append(rule)
                self.rules_list.append(rules_list)

    def __save(self):
        common.save_json(self.output_folder + "/rules_list.json", self.rules_list,
                         encoding=setting.OUTPUT_JSON_ENCODING)
        common.save_json(self.output_folder + "/api_info.json", self.api_info, encoding=setting.OUTPUT_JSON_ENCODING)
        common.save_json(self.output_folder + "/origin_json.json", self.json_data,
                         encoding=setting.OUTPUT_JSON_ENCODING)
        static_exp ={"time":{}}
        static_exp["document_size"] = self.document_size
        static_exp["document_tree_length"] = self.document_tree_length
        static_exp["rules_list_lines"] = len(open(self.output_folder + "/rules_list.json", 'r',encoding='utf-8').readlines())
        static_exp["api_info_lines"] = len(open(self.output_folder + "/api_info.json", 'r',encoding='utf-8').readlines())

        static_exp["time"][self.time_crawl.name] = self.time_crawl.getInterval()
        static_exp["time"][self.time_form_handle.name] = self.time_form_handle.getInterval()
        static_exp["time"][self.time_web_segmentation.name] = self.time_web_segmentation.getInterval()
        static_exp["time"][self.time_web_seg_sort.name] = self.time_web_seg_sort.getInterval()
        static_exp["time"][self.time_generate_documents.name] = self.time_generate_documents.getInterval()
        common.save_json(self.output_folder + "/static_exp.json", static_exp,
                         encoding=setting.OUTPUT_JSON_ENCODING)



    def __output_images(self):
        tmp_path = self.output_folder + "/tmp"
        path = self.output_folder + "/images"
        common.prepare_clean_dir(tmp_path)
        common.prepare_clean_dir(path)
        for segment in self.json_data["segments"]:
            for record in segment["records"]:
                for i, image in enumerate(record["images"]):
                    try:
                        file_name = "%s_%s" % (record["record_id"], i)
                        source_file_name_only = tmp_path + "/" + file_name
                        original_extension = image["src"].split('/')[-1].split('.')[-1].split("?")[0]
                        source_file_name = source_file_name_only + "." + original_extension
                        target_file_name = path + "/" + file_name + "." + setting.OUTPUT_IMAGE_TYPE

                        r = requests.get(image["src"], stream=True, headers={'User-agent': 'Mozilla/5.0'})  # get方法得到资源
                        if r.status_code == 200:
                            with open(source_file_name, 'wb') as f:
                                r.raw.decode_content = True
                                shutil.copyfileobj(r.raw, f)
                        else:
                            continue
                        # 写入图片信息
                        [R, G, B] = [int(a) for a in image["bg_color"].split(",")]
                        im = Image.open(source_file_name).convert('RGBA')
                        bg = Image.new("RGB", im.size, (R, G, B))
                        bg.paste(im, im)
                        im = bg
                        im.save(target_file_name)
                        image["path"] = target_file_name
                    except Exception:
                        pass

        common.save_json(self.output_folder + "/result.json", self.json_data, encoding=setting.OUTPUT_JSON_ENCODING)
        shutil.rmtree(tmp_path)
        # 递归的去删除文件

    # 去除无用的路径信息
    def remove_slash(self, path):
        for i in range(len(path)):
            if path.endswith('/'):
                path = path[:-1]
            if path.endswith('\\'):
                path = path[:-1]
        return path

    # 处理表单信息
    def __read_form_rules_and_type(self):
        if self.form_check == 1:  # 如果有参数
            time.sleep(3)  # 等待3s保证执行完成
            self.form_list = common.load_json(self.form_path, encoding=setting.OUTPUT_JSON_ENCODING)  # 这里改成相应地址就能复用
            input_list = self.form_list["forms"][self.form_list["main_form_index"]]["input_list"]
            form_type = self.form_list["forms"][self.form_list["main_form_index"]]["type"]  # form类型，是否为嵌套在iframe里的
            slot = ""
            if form_type == 1:  # 如果是iframe中的form
                iframe = self.form_list["forms"][self.form_list["main_form_index"]]["css_selector"].split(">f>")[
                    0]  # iframe的selector
                slot = 'document.querySelector("' + iframe + '").contentWindow.'
            try:
                button = self.form_list["forms"][self.form_list["main_form_index"]]["submit_button_list"][
                    self.form_list["forms"][self.form_list["main_form_index"]]["main_btn_index"]]
            except:
                pass
            try:
                for input in input_list:  # 模拟表单操作
                    if form_type == 1:  # form表单情况下取后面的selector
                        input["css_selector"] = input["css_selector"].split(">f>")[1]

                    if input["type"] == "radio" or input["type"] == "checkbox":  # 这两种情况单独处理
                        if input["value"] == "true":  # 只要不是true就是false，前端也要随着更新
                            self.browser.execute_script(
                                slot + 'document.querySelector("' + input["css_selector"] + '").checked = true')
                        else:
                            self.browser.execute_script(
                                slot + 'document.querySelector("' + input["css_selector"] + '").checked = false')
                        continue
                    if input["type"] == "select" or input["type"] == "datalist":
                        self.browser.execute_script(
                            slot + 'document.querySelector("' + input["css_selector"] + '").selectedIndex = ' + str(
                                input["value"]))
                        continue
                    if input["type"] != "hidden":  # hidden一般不要动
                        # print('document.querySelector("' + input["css_selector"] + '").value = "'+input["value"] +'"')
                        self.browser.execute_script(
                            slot + 'document.querySelector("' + input["css_selector"] + '").value = "' + input[
                                "value"] + '"')
                    time.sleep(0.2)
                        # self.browser.find_element_by_css_selector(input["css_selector"]).send_keys(input["value"])
                time.sleep(1)  # 等待1s
                if form_type == 1:  # form表单情况下取后面的selector
                    button["css_selector"] = button["css_selector"].split(">f>")[1]
                self.browser.execute_script(
                    slot + 'document.querySelector("' + button["css_selector"] + '").click()')  # 点击按钮
                time.sleep(1 + self.interval)  # 等待1s+相应等待时间
            except:
                pass  # 填写表单过程中出现任何问题，无视
            self.browser.switch_to.window(self.browser.window_handles[-1])  # 切换到最新窗口
            self.page = pq(self.browser.page_source.replace('xmlns', 'another_attr'))  # pyquery
            self.th_num = self.page("th").length
            self.soup = BeautifulSoup(self.browser.page_source, 'html.parser')  # 标准库方式载入页面源代码
            try:
                self.page_height = self.browser.find_element_by_tag_name("body").rect["height"]  # 找到body大小
                self.browser.set_window_size(setting.SCREEN_WIDTH, self.page_height)  # 设置窗口大小
            except:
                pass

            self.browser.save_screenshot(self.output_folder + "/screenshot.png")  # 截屏
            print("Input success")
