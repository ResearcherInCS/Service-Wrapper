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

from __future__ import unicode_literals
import pymysql
import json
import time
import requests

from app.models.ServiceDetailEntity import ServiceDetails
class MYSQL:
    def __init__(self):
        self.me = ''

    def deleteOneToGrid_API(self, service):
        service_exist = ServiceDetails.objects(api_address=service.url).first()
        if not service_exist:
            pass
        else:
            service_exist.delete()

    def all_service(self):
        sers = ServiceDetails.objects().all()
        return sers;

    def insertOneToGrid_API(self, service, update=False):
        arguments = service.api_request_parameters_candidate
        arguments_upload = []
        for argument in arguments:
            must = "否"
            if argument["required"]:
                must = "是"
            arguments_upload_one = {
                "名称": argument["query_name"],
                "类型": argument["type"],
                "必填": must,
                "示例值": argument["example"],
                "描述": argument["description"]
            }
            arguments_upload.append(arguments_upload_one)
        arguments_upload = json.dumps(arguments_upload, ensure_ascii=False)    ## arguments

        result_argument_ = service.candidate[service.main_sec_id]
        result_arguments = []
        for result_o in result_argument_:
            if result_o["select"] == 1:
                result_argument = {
                    "名称":result_o["name"],
                    "类型":result_o["type"],
                    "示例值":result_o["example"],
                    "描述":result_o["description"]
                }
                result_arguments.append(result_argument)

        result_arguments = json.dumps(result_arguments, ensure_ascii=False)    ## result_argument

        result_ex = {
            "status": 200,
            "msg": "请求成功，共处理1页.",
            "data": service.api_result_example
        }
        result = json.dumps(result_ex, ensure_ascii=False)   ## result
        error_code = [
                         {'错误码': 10000, '说明': '请求成功,共处理x页,其中第a,b页处理失败. 或者 请求成功,共处理x页'}, \
                         {'错误码': 4000, '说明': 'Parameters error'}, \
                         {'错误码': 4001, '说明': '缺少必须的参数'}, \
                         {'错误码': 5000, '说明': 'Service does not exist'}, \
                         {'错误码': 5001, '说明': 'The service already exists'}, \
                         {'错误码': 6001, '说明': '缺失api_crawl_rules_link文件或candidate项，无法处理网页'}, \
                         {'错误码': 7000, '说明': '爬虫超时'}, \
                         {'错误码': 7001, '说明': '爬虫失败，超时或请求错误'}, \
                         {'错误码': 8000, '说明': '服务器请求爬虫规则失效'}, \
                         {'错误码': 8001, '说明': '解析失败，网页信息错误'}
                     ]
        error_code = json.dumps(error_code, ensure_ascii=False)   ## error_code
        if not update:  #直接上传的
            servicedetail = ServiceDetails(api_id=int(service.api_id),
                                           name=service.api_name,
                                           api_address=service.url,
                                           api_call_way='HTTP GET',
                                           api_introduction=service.api_description,
                                           arguments=arguments_upload,
                                           result_arguments=result_arguments,
                                           error_code=error_code,
                                           result=result,
                                           return_style="JSON",
                                           call_example=service.url+"?__max_page=1",
                                           create_time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())).save()
        else:      # 修改的
            service_exist = ServiceDetails.objects(api_address=service.url).first()
            if not service_exist:
                pass
            else:
                service_exist.update(api_id=int(service.api_id),
                                     name=service.api_name,
                                     api_address=service.url,
                                     api_call_way='HTTP GET',
                                     api_introduction=service.api_description,
                                     arguments=arguments_upload,
                                     result_arguments=result_arguments,
                                     error_code=error_code,
                                     result=result,
                                     return_style="JSON",
                                     call_example=service.url+"?__max_page=1",
                                     update_time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
