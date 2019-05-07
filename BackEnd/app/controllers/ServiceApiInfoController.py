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

from app import app
from flask_cors import CORS
from app.response.Respone import RESPONSEENUM as ReNum
from app.models.ServiceDetailEntity import ServiceDetails

CORS(app, resources=r'/*')
@app.route('/services', methods=['GET'])
def services_all():
    sers = ServiceDetails.objects().all()
    return ReNum.SUCCESS.update(sers).value()

@app.route('/services/<api_id>', methods=['GET'])
def services_one(api_id):
    sers = ServiceDetails.objects(api_id=api_id).first()
    if sers:
        return ReNum.SUCCESS.update(sers).value()
    else:
        return ReNum.SERV_NO_EXIST.value()
