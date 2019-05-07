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

from app import db

class Api(db.Document):
    # 字段
    api_name = db.StringField()              # 服务名称
    api_description = db.StringField()       # 服务描述
    api_id = db.SequenceField()              # 服务唯一标示
    url = db.URLField()                      # 自身已经封装成的可以调用的url地址
    api_url = db.URLField()                 # 转接url地址

    img_link = db.URLField()
    json_link = db.URLField()

    api_crawl_rules_link = db.URLField()                   # 爬虫规则列表链接

    candidate = db.ListField()              # api参数列表

    main_sec_id = db.IntField()

    api_network = db.ListField()            # 网页可能有效的network请求

    api_result_example = db.ListField()

    form_rules_link = db.URLField()        # check click button的json链接

    api_request_parameters_candidate = db.ListField()  # 调用服务时可以使用的参数
    # {"type":"text",
    #  "query_name":"",
    #  "required":false/true, 是否必须
    #  "level":0/1/2,   0-系统级（__max_page）,1-查询级（需要填充到输入框中的）,2-返回级（返回参数中的）
    #   "example":
    #   "description"
    # }

    def __str__(self):
        return "service:{} - url:{}".format(self.api_name, self.url)
