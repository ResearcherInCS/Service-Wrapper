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

from flask import jsonify

class RESPONSE:
    def __init__(self, jsonify, code = 200, header = {'Content-Type': 'application/json;chaset=utf-8'}):
        self.jsonify = jsonify
        self.code = code
        self.header = header

    def value(self):
        return self.jsonify.jonsified(), self.code, self.header

    def update(self, data='', msg=''):
        self.add_msg(msg)
        self.update_data(data)
        return self

    def add_msg(self, msg):
        self.jsonify.add_msg(msg)

    def update_data(self, data):
        self.jsonify.update_data(data)

    def __str__(self):
        return "data:{} - code:{} - header - {}".format(self.jsonify, self.code, self.header)

class JSONIFY:
    def __init__(self, status, msg, data=''):
        self.status = status
        self.msg = msg
        self.data = data

    def add_msg(self, msg):
        self.msg = self.msg + msg
    def update_data(self,data):
        self.data = data

    def jonsified(self):
        return jsonify({'status': self.status, 'msg': self.msg, 'data': self.data})

'''
[
    {'错误码': 10000, '说明': '请求成功,共处理x页,其中第a,b页处理失败. 或者 请求成功,共处理x页'}, \
    {'错误码': 4000, '说明': 'Parameters error'}, \
    {'错误码': 4001, '说明': '缺少必须的参数'}, \
    
    {'错误码': 5000, '说明': 'Service does not exist'}, \
    {'错误码': 5001, '说明': 'The service already exists'}, \
    
    {'错误码': 6001, '说明': '缺失api_crawl_rules_link文件或candidate项，无法处理网页'}, \
    {'错误码': 7000, '说明': '爬虫超时'}, \  
    {'错误码': 7001, '说明': '爬虫失败，超时或请求错误'}, \
    {'错误码': 8000, '说明': '服务器请求爬虫规则失效'}, \
    {'错误码': 8001, '说明': '解析失败，网页信息错误'}, \
]    
'''
class RESPONSEENUM():
    SUCCESS =  RESPONSE(JSONIFY(10000, 'Request success', ''))

    PARAM_ERR = RESPONSE(JSONIFY(4000, 'Parameters error', ''))
    PARAM_LACK = RESPONSE(JSONIFY(4001, 'Missing the required parameters', ''))
    SERV_NO_EXIST = RESPONSE(JSONIFY(5000, 'Service does not exist', ''))
    SERV_EXISTED = RESPONSE(JSONIFY(5001, 'The service already exists', ''))

    INVOKE_LACK_DOC = RESPONSE(JSONIFY(6001, 'The api_crawl_rules_link file or candidate item is missing and the web page cannot be processed', ''))

    CRAW_TIME_OUT = RESPONSE(JSONIFY(7000, 'The crawler timeout'))
    CRAW_ERROR = RESPONSE(JSONIFY(7001, 'Crawler failed, timeout or request error'))

    REQUEST_ERROR = RESPONSE(JSONIFY(8000, 'The server request crawler rule failed'))
    PAGE_PAESE_FAIL = RESPONSE(JSONIFY(8001, 'Parsing failed, web page information error'))
