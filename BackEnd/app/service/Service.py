# Copyright 2018 Xiya Lyu
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from html.parser import HTMLParser
import bs4
from bs4 import BeautifulSoup
from pyquery import PyQuery as pq
from urllib.parse import urljoin
import os
from app.service import setting as setting
import re, time


class Crawler:
    def __init__(self,log):  ## log should be app.logger
        # self.proxy_path = os.path.dirname(__file__) + "/browsermob-proxy-2.1.4/bin/browsermob-proxy"
        # self.server = Server(self.proxy_path)
        # self.server.start()
        # self.proxy = self.server.create_proxy()
        #
        # self.proxy.new_har(options={
        #     'captureContent': True
        # })

        options = webdriver.ChromeOptions()

        if setting.PRODUCTION:
            options.binary_location = setting.CHROME_BINARY_LOCATION_PRODUCTION
            path = setting.DRIVER_PATH_PRODUCTION
        else:
            options.binary_location = setting.CHROME_BINARY_LOCATION_LOCAL
            path = os.path.dirname(__file__) + setting.DRIVER_PATH_PRODUCTION_LOCAL  # upload 修改

        # options.add_argument("--proxy-server={0}".format(self.proxy.proxy))
        # print(self.proxy.proxy)
        options.add_argument('--headless')  # 不显示浏览器
        prefs = {                           ## 设置不加载图片
            'profile.default_content_setting_values': {
                'images': 2
            }
        }
        options.add_experimental_option('prefs', prefs)
        self.browser = webdriver.Chrome(chrome_options=options, executable_path=path)#setting.DRIVER_PATH) ##"/usr/bin/chromedriver"
        self.browser.set_window_size(setting.SCREEN_WIDTH, 800)  # set the window size that you need
        self.parser = HTMLParser()
        self.max_page = 1
        self.current_page = 1
        self.max_page_set = 1  # 用户指定的max_page
        self.max_page_set_flag = False # 用户是否设定了max_page

        self.default_max_page = 5   # 是否加载全部网页， 默认情况下是5页； 当用户不设置max_page时，该项起作用；设置max_page,该项不起作用

        self.click_nextpage_css_selector = None
        self.log = log
        self.log.info(os.path.abspath('.'))

        self.api_request = {}

        self.css_selc = None
        self.form_list = None
        self.input_key = None
        self.input_value = None

        self.last_page = None

        self.iframe_ex = False  #是否有iframe，有的话要特殊处理
        self.iframe_addr = ""


    def getContentText(self):
        """
        step 7 简单的获取目标数据的函数
        其中 targetUrl 为浏览器获取对应数据调用的url，需要用正则表达式表示
        """
        if self.proxy.har['log']['entries']:
            for loop_record in self.proxy.har['log']['entries']:
                try:
                    if self.filer_aviable_api(loop_record["request"]['url']) and loop_record["request"]['url'] not in self.api_request.keys():
                        self.api_request[loop_record["request"]['url']] = loop_record["response"]['content']
                except Exception as err:
                    self.log.error(repr(err))
                    continue

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
        for parent in node.parents:
            if parent.name == "[document]":
                break
            path.insert(0, self.__get_element(parent))
        return ' > '.join(path)  # 一路拼接即得到了css selector

    def find_pages(self):
        '''
        找到翻页所在的位置
        :return: 下一页那一栏的css_select 或者 None
        '''
        try:
            self.soup = BeautifulSoup(self.browser.page_source, 'html.parser')  # 标准库方式载入页面源代码
            tagbody = self.soup.find("body")  # 得到body体
            allnodes = [tagbody]  # put body block into allnodes list
            tagbody["lid"] = str(-1)
            tagbody["sn"] = str(1)
            i = 0
            while len(allnodes) > i:
                children = []
                for child in allnodes[i].children:
                    if isinstance(child, bs4.element.Tag):  # 如果直接子节点是TAG类型，则放入children列表，即得到正文中的所有显示出的信息（去除注释及其他代码）
                        text = child.text
                        if ("1" in text) and (("下一页" in text) or ("next" in text) or ("last" in text) or ("尾页" in text)):
                            children.append(child)
                sn = len(children)

                for child in children:
                    child["lid"] = str(i)  # 广度优先搜索顺序
                    child["sn"] = str(sn)  # 本层节点数目
                    # 注意，这里一旦修改了节点属性，则数组里所有包含此节点的属性都会被修改！！！！！
                    allnodes.append(child)  # 加入allnodes节点
                i += 1
            next_page = allnodes[len(allnodes) - 1]
            if ("1" in next_page.text) and (("下一页" in next_page.text) or ("尾页" in next_page.text) or ("next" in next_page.text) or (
                    "last" in next_page.text)):
                x = self.__get_css_selector(next_page)
                return self.__get_css_selector(next_page)
            else:
                return None
        except:
            return None

    def next_page(self):
        next_page_css_selector = self.find_pages()

        self.click_nextpage_css_selector = next_page_css_selector
        self.update_max_page()
        pass

    def update_max_page(self):
        could_continue = False  # 这里用来判断真正是表示页数的数据，假设页数一定在首页之后，如果有首页，则首页后面的数字才表示页数多少；
        if self.click_nextpage_css_selector:
            pages = self.page(self.click_nextpage_css_selector)
            pages_ = pages.children().text().split(" ")

            if '首页' in pages.children().text():
                could_continue = False
            else:
                could_continue = True

            for child in pages_:
                if child and child.isdigit() and could_continue:
                    if self.max_page < int(child): self.max_page = int(child)
                elif child:
                    if child == "首页":
                        could_continue = True
                    elif child == "尾页":
                        could_continue = False
                    elif could_continue:
                        child_ = child.split("\n")
                        for child_child in child_:
                            if child_child and child_child.isdigit():
                                if self.max_page < int(child_child): self.max_page = int(child_child)

    def click_next_page(self):
        if self.current_page == 1:
            self.current_page = self.current_page + 1
        else:
            if self.judge_whether_final_page():
                try:
                    next_pages = self.browser.find_element_by_css_selector(self.click_nextpage_css_selector)
                    to_click = next_pages.find_element_by_partial_link_text(str(self.current_page))
                    to_click.click()
                    while self.last_page == self.browser.find_element_by_css_selector(self.css_selc):
                        pass
                    self.last_page = self.browser.find_element_by_css_selector(self.css_selc)
                    # time.sleep(1)
                    # if self.css_selc:
                    #     WebDriverWait(self.browser, 10).until(
                    #         EC.presence_of_element_located((By.CSS_SELECTOR, self.css_selc)))
                except:
                    self.log.error("第"+str(self.current_page)+"页 元素未加载成功") # 错误日志
                    self.current_page = self.current_page + 1
                    return False, str(self.current_page-1)   ## 网页信息失败的返回
                # self.getContentText()
                self.update_max_page()
                self.page = pq(self.browser.page_source.replace('xmlns', 'another_attr'))

                self.current_page = self.current_page + 1
            else:
                return False, ""  ## 已经达到了最后页的返回
        return True,""  ## 正常的返回

    def filer_aviable_api(self, api_value_ori):
        """
        筛选api信息是否是可能有用的信息，现在如果以ico,png,js,gif,css,jpeg结尾的均认为不是有用的信息,且请求地址和网页地址完全一致的话就不是api所以要删除
        :param api_value_ori:
        :return: True False
        """
        api_value = api_value_ori.lower()
        # self.log.info(api_value_ori) #api_value_ori == self.url or
        if api_value.endswith(".jpg") \
                or api_value.endswith(".ico") or api_value.endswith(".png") \
                or api_value.endswith(".js") or api_value.endswith(".gif") \
                or api_value.endswith(".css") or api_value.endswith(".jpeg") \
                or api_value.endswith(".htm") or api_value.endswith(".html"):
            return False
        else:
            if re.search(re.compile("http://.*((\.gif\?)|(\.js\?)).*"), api_value):
                return False
            return True

    def _get_css(self, baseurl, css_selector):
        try:
            url = self.browser.find_element_by_css_selector(css_selector).value_of_css_property(
                "background-image")  # 得到此属性
            if url != "none":

                url = url.replace('url(', '').replace(')', '').replace('\'', '').replace('\"', '')
                url = urljoin(baseurl, url)
                return url
            return ""
        except:
            return ""

    def __read_form_rules_and_type(self):
        input_list_ori = self.form_list["forms"][self.form_list["main_form_index"]]["input_list"]

        form_type = self.form_list["forms"][self.form_list["main_form_index"]]["type"]
        slot = ""
        if form_type == 1:
            iframe = self.form_list["forms"][self.form_list["main_form_index"]]["css_selector"].split(">f>")[
                0]  # iframe的selector
            slot = 'document.querySelector("' + iframe + '").contentWindow.'

        input_list_query_name = [ i["query_name"] for i in input_list_ori ]
        input_list = []
        for num in range(len(self.input_key)):
            eve_input_key = self.input_key[num]
            eve_input_value = self.input_value[num]
            eve_input_list = input_list_ori[input_list_query_name.index(eve_input_key)]
            eve_input_list["value"] = eve_input_value
            input_list.append(eve_input_list)
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
                        slot + 'document.querySelector("' + input["css_selector"] + '").value = "' + input["value"] + '"')
            time.sleep(1)  # 等待1s
            self.browser.execute_script(
                slot + 'document.querySelector("' + button["css_selector"] + '").click()')  # 点击按钮
            time.sleep(1)  # 等待1s
        except:
            pass  # 填写表单过程中出现任何问题，无视
        self.browser.switch_to.window(self.browser.window_handles[-1])  # 切换到最新窗口

        if self.iframe_ex:
            self.browser.switch_to.frame(
                self.browser.find_element_by_css_selector(self.iframe_addr))

        self.page = pq(self.browser.page_source.replace('xmlns', 'another_attr'))  # pyquery
        self.last_page = self.browser.find_element_by_css_selector(self.css_selc)
        self.next_page()  # 找到点击的位置，找到最大页数和css_选择器
        try:
            self.page_height = self.browser.find_element_by_tag_name("body").rect["height"]  # 找到body大小
            self.browser.set_window_size(setting.SCREEN_WIDTH, self.page_height)  # 设置窗口大小
        except:
            pass

    def segment(self, url):
        self.url = url
        self.log.info("Crawl HTML Document from %s,please wait for about 60s(max 120s)" % self.url)
        return self.__crawler()  # 爬取页面

    def __crawler(self):
        self.browser.set_page_load_timeout(60)
        try:
            if self.form_list["form_check"] == 1:  # 如果有参数, 即动态页面
                self.browser.get(self.url)

                return self.__read_form_rules_and_type()
            else:   # 如果没有参数，即静态页面
                self.browser.get(self.url)
                # WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,self.css_selc)))

                if self.iframe_ex:
                    self.browser.switch_to.frame(
                        self.browser.find_element_by_css_selector(self.iframe_addr))

                # self.getContentText()  ## 将network信息存入api_request
                self.page = pq(self.browser.page_source.replace('xmlns', 'another_attr')) # 标准库方式载入页面源代码

                self.last_page = self.browser.find_element_by_css_selector(self.css_selc)
                self.next_page()   # 找到点击的位置，找到最大页数和css_选择器
                try:
                    self.page_height = self.browser.find_element_by_tag_name("body").rect["height"]  # 找到body大小
                    self.browser.set_window_size(setting.SCREEN_WIDTH, self.page_height)  # 设置窗口大小
                except:
                    pass
        except TimeoutException:
            self.log.warning("503 " + "request time out,task end,please retry")
            return "timeout"

    def judge_whether_final_page(self):
        """
        判断是否达到了最后一页，最后一页指实际的最后一页和指定的最后一页
        当没达到的时候，返回True
        达到了的时候，返回False
        :return:
        """
        if not self.max_page_set_flag:
            if self.current_page > self.default_max_page:
                return False

        if self.max_page_set_flag:
            if self.current_page <= self.max_page and self.current_page <= self.max_page_set:
                return True
            else:
                return False
        else:
            if self.current_page <= self.max_page:
                return True
            else:
                return False

    def _end(self):
        # try:
        #     self.proxy.close()
        #     self.server.process.terminate()
        #     self.server.process.wait()
        #     self.server.process.kill()
        # except:
        #     pass

        self.browser.quit()


# 根据html源码和rank得到text文本
def get_text_from_rank(htm, rank):
    i = 0
    htm = BeautifulSoup(htm, 'html.parser')  # html转换成rank
    for text in htm.stripped_strings:  # 当一个Tag对象有多个子节点时，可以用.strings方法再通过遍历获得所有子节点的内容。
        if i == rank:
            return text
        i += 1

def image_filter(image, page_pyquery, api_parameters, api_url, crawl):
    css_img_result = pq(page_pyquery(image["css_selector"])[0])
    id = image["id"]
    type = image["type"]

    parameter = api_parameters[id]

    src = css_img_result.attr("src")
    alt = css_img_result.attr("alt")
    title = css_img_result.attr("title")
    if type == "img":
        if not src:
            src = ""
        else:
            if not src.startswith("http"):
                src = urljoin(api_url, "/" + src)
        if not alt:
            alt = ""
        if not title:
            title = ""
    elif type == "background_img":
        src = crawl._get_css(api_url, image["css_selector"])
        if not alt:
            alt = ""
        if not title:
            title = ""
    return {"src": src,
             "alt": alt,
             "title": title}, parameter

def text_filter(text, page_pyquery, api_parameters):
    css_text_result = pq(page_pyquery(text["css_selector"])[0]).html()
    id = text["id"]
    rank = text["rank"]
    parameter = api_parameters[id]
    if not css_text_result:
        return "", parameter
    return get_text_from_rank(css_text_result, rank), parameter

def select_result_parameter(request_parameters, result_demo):
    """
    选择在参数集里面，在结果中存在该参数属性的参数子集合;同时筛选出是请求参数，但是不在返回属性中的，且不在超级请求参数中的参数
    :return: 交集和差集
    """
    unions_list = []
    cha_set_list = []
    for request_parameter in request_parameters:
        # 需要迭代判断一下这个到底在result里面有没有这个路径，和之后的那个判断其实是一致的
        if iterator_judge_no_value(request_parameter, result_demo):
            unions_list.append(request_parameter)
        else:
            if request_parameter[0] not in setting.HYPERPARAMETER:
                cha_set_list.append(".".join(request_parameter))
    return unions_list, cha_set_list

def iterator_judge_no_value(lists, dicts):
    if type(dicts) != dict:
        if len(lists) == 0:
            return True
        else:
            return False
    else:
        if len(lists) >= 1:
            if lists[0] in dicts.keys():
                return iterator_judge_no_value(lists[1:], dicts[lists[0]])
            else:
                return False
        else:
            return False


def iterator_judge(lists, dicts, value):
    if type(dicts) != dict :
        if dicts == value and len(lists) == 0:
            return True
        else :
            return False
    else:
        if len(lists) >= 1:
            if lists[0] in dicts.keys():
                return iterator_judge(lists[1:], dicts[lists[0]], value)
            else:
                return False
        else:
            return False

def func():
    name = "lxy"
    return name,""

if __name__ == "__main__":
    # requ = ["qingqiu","test"]
    # value = "sss"
    # dictss = {
    #     "qingqiu":{
    #         "test": "hahha"
    #     }
    # }
    #
    # print(iterator_judge(requ, dictss, value))

    print(func()[1])
