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

class ServiceDetails(db.Document):

    api_id = db.IntField()
    name = db.StringField()            # 参数名称

    api_address = db.StringField()            # 参数类型

    api_call_way = db.StringField()
    api_introduction = db.StringField()

    arguments = db.StringField()
    result_arguments = db.StringField()
    error_code = db.StringField()
    result = db.StringField()
    return_style = db.StringField()
    call_example = db.StringField()
    create_time = db.StringField()
    update_time = db.StringField()
    def __str__(self):
        return "service:{} - url:{}".format(self.name, self.description)
