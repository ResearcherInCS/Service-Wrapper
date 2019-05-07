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

from app.service.Service import Crawler, image_filter, text_filter, select_result_parameter, iterator_judge, get_text_from_rank
from app import app
from app.service.Util import shutdown_crawl
from pyquery import PyQuery as pq
from urllib.parse import urljoin
from app.service.Util import read_file_as_str
import json
class CallService:
    def __init__(self, service):
        self.service = service

    def set_required_parameter(self):
        ## level_1 parameters
        # 选出在request_parameters中属于level1的那些参数
        required_parameters = []
        for request_parameter in self.service.api_request_parameters_candidate:
            if request_parameter["required"]:
                required_parameters.append(request_parameter)
        self.crawl.input_key = []
        self.crawl.input_value = []
        for level_1_parameter in required_parameters:
            self.crawl.input_key.append(level_1_parameter["query_name"])
            self.crawl.input_value.append(level_1_parameter["example"])

    def wait_condition(self):
        """
        设置加载网页时的等待条件
        :param api_crawl_rules:
        :return:
        """
        if len(self.api_crawl_rules) > 0:
            wait_rule = self.api_crawl_rules[0]
            wait_images = wait_rule["images"]
            wait_texts = wait_rule["texts"]
            wait_links = wait_rule["links"]
            if len(wait_texts) > 0:
                self.crawl.css_selc = wait_texts[0]["css_selector"]
            elif len(wait_images) > 0:
                self.crawl.css_selc = wait_images[0]["css_selector"]
            elif len(wait_links) > 0:
                self.crawl.css_selc = wait_links[0]["css_selector"]

            if self.crawl.css_selc:
                if self.crawl.css_selc.find(">f>") >= 0:  # 对iframe中元素的特殊处理
                    self.crawl.iframe_addr = self.crawl.css_selc.split(">f>")[0]
                    self.crawl.css_selc = self.crawl.css_selc.split(">f>")[1]
                    self.crawl.iframe_ex = True

    def analyze_crawer_result(self):
        results = []
        try:
            cram_click_next_page, data_error = self.crawl.click_next_page()
            if cram_click_next_page:
                page_pyquery = self.crawl.page  ## 页面page
                for rule in self.api_crawl_rules:
                    images = rule["images"]
                    texts = rule["texts"]
                    links = rule["links"]
                    result = {"record_id": rule["record_id"]}
                    for image in images:
                        if self.crawl.iframe_ex and image["css_selector"].find('>f>')>=0:
                            image["css_selector"] = image["css_selector"].split(">f>")[1]
                        if not page_pyquery(image["css_selector"]) or len(page_pyquery(image["css_selector"])) == 0:
                            continue

                        if not self.crawl.css_selc:
                            self.crawl.css_selc = image["css_selector"]

                        res_value, parameter = image_filter(image, page_pyquery, self.service.candidate[self.service.main_sec_id], self.service.api_url, self.crawl)
                        if parameter["select"] == 1:
                            result[parameter["name"]] = res_value

                    for text in texts:
                        if self.crawl.iframe_ex and text["css_selector"].find('>f>')>=0:
                            text["css_selector"] = text["css_selector"].split(">f>")[1]

                        if not page_pyquery(text["css_selector"]) or len(page_pyquery(text["css_selector"])) == 0:
                            continue
                        if not self.crawl.css_selc:
                            self.crawl.css_selc = text["css_selector"]
                        text_value, parameter = text_filter(text, page_pyquery, self.service.candidate[self.service.main_sec_id])

                        if parameter["select"] == 1:
                            result[parameter["name"]] = text_value

                    for link in links:
                        if self.crawl.iframe_ex and link["css_selector"].find('>f>')>=0:
                            link["css_selector"] = link["css_selector"].split(">f>")[1]

                        if not page_pyquery(link["css_selector"]) or len(page_pyquery(link["css_selector"])) == 0:
                            continue
                        if not self.crawl.css_selc:
                            self.crawl.css_selc = link["css_selector"]
                        css_link_result = pq(page_pyquery(link["css_selector"])[0])
                        id = link["id"]
                        link_images = link["images"]
                        link_texts = link["texts"]

                        parameter = self.service.candidate[self.service.main_sec_id][id]
                        result[parameter["name"]] = {}

                        for link_image in link_images:
                            if self.crawl.iframe_ex and link_image["css_selector"].find('>f>')>=0:
                                link_image["css_selector"] = link_image["css_selector"].split(">f>")[1]

                            if not page_pyquery(link_image["css_selector"]) or len(
                                    page_pyquery(link_image["css_selector"])) == 0:
                                continue
                            link_image_res_value, link_image_parameter = image_filter(link_image, page_pyquery, self.service.candidate[self.service.main_sec_id], self.service.api_url, self.crawl)
                            if link_image_parameter["select"] == 1:
                                result[parameter["name"]][link_image_parameter["name"]] = link_image_res_value
                        for link_text in link_texts:
                            if self.crawl.iframe_ex and link_text["css_selector"].find('>f>')>=0:
                                link_text["css_selector"] = link_text["css_selector"].split(">f>")[1]

                            if not page_pyquery(link_text["css_selector"]) or len(
                                    page_pyquery(link_text["css_selector"])) == 0:
                                continue
                            link_text_value, link_parameter = text_filter(link_text, page_pyquery, self.service.candidate[self.service.main_sec_id])
                            if link_parameter["select"] == 1:
                                result[parameter["name"]][link_parameter["name"]] = link_text_value
                        if parameter["select"] == 1:
                            if css_link_result.attr("href").startswith("http"):
                                result[parameter["name"]]["href"] = css_link_result.attr('href')
                            else:
                                result[parameter["name"]]["href"] = urljoin(self.service.api_url, "/" + css_link_result.attr('href'))

                    results.append(result)
            return results
        except:
            return results


    def call_only_one_page_for_getting_result_demo(self):
        api_crawl_rules_link = self.service.api_crawl_rules_link
        form_rules_link = self.service.form_rules_link
        api_parameters = self.service.candidate[self.service.main_sec_id]
        api_url = self.service.api_url
        if api_crawl_rules_link and api_parameters:
            try:

                form_rules_link_ex = api_crawl_rules_link.split('/statics/', 1)[1]
                strss = read_file_as_str("static/" + form_rules_link_ex)
                api_crawl_rules_two = json.loads(strss)

                # api_crawl_rules_two = requests.get(api_crawl_rules_link).json()
                self.api_crawl_rules = api_crawl_rules_two[self.service.main_sec_id]
            except:
                return "Error by service details"

            try:
                self.crawl = Crawler(app.logger)

                self.crawl.max_page_set = 1
                self.crawl.max_page_set_flag = True  # 设置页数为1

                self.set_required_parameter()    # 设置必要的参数
                self.wait_condition()   # 设置加载网页的等待条件

                if form_rules_link:
                    form_rules_link_ex = form_rules_link.split('/statics/', 1)[1]
                    strss = read_file_as_str("static/" + form_rules_link_ex)
                    self.crawl.form_list = json.loads(strss)
                    # self.crawl.form_list = requests.get(form_rules_link).json()

                time_out_judge = self.crawl.segment(api_url)

                if time_out_judge == "timeout":
                    return "Error by crawler timeout"
            except Exception as e:
                shutdown_crawl(self.crawl)
                app.logger.error(repr(e))
                return "Error by unknown crawler problem"

            results = self.analyze_crawer_result()

            try:  ##  track 1: dot cant be a key in mongodb,for example {"3.4":dsada}
                numb = 3
                if len(results) < 3:
                    numb = len(results)
                result_example = results[:numb]
                self.service.update(api_result_example = result_example)
                return "Success"
            except:
                return "Error by update"
        else:
            return "Error by missing service message"

    def shutDown(self):
        self.crawl._end()