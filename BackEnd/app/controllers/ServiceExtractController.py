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
from flask import jsonify, request, send_file, Response
import os
import time
import random
import json
import numpy as np
from PIL import Image
import app.service.setting as setting
from app.service.Util import read_file_as_str
CORS(app, resources=r'/*')
@app.route('/servicewrapper', methods=['GET', 'POST'])
def device_get():
    if request.method == 'GET':
        if request.args.get('url'):
            message = request.args.get('url').replace("&", "\&")
            if request.args.get('form_check'):  # 是否检测表格
                form_check = str(request.args.get('form_check'))
            else:
                form_check = "0"

            poke = str(int(time.time())) + str(random.randint(1, 10000))

            command = 'python3 app/service/segment_demo.py ' + message + ' ' + poke + ' ' + form_check + ' "form_list.json" &'
            os.system(command)
            return setting.SERVER_ADDRESS+"statics/" + poke + "/process.log"

        else:
            app.logger.error("503 wrong information")
            return "503 wrong information"
    elif request.method == "POST":
        # try:
        data = request.json
        message = data['url'].replace("&", "\&")
        form_check = str(data['form_check'])
        poke = str(int(time.time())) + str(random.randint(1, 10000))
        path = 'static/form_json/' + poke + '.json'  # 存储此json
        with open(path, 'w', encoding='utf-8') as outfile:
            json.dump(data, outfile, ensure_ascii=False, cls=MyEncoder, skipkeys=True)
        time.sleep(1)
        command = 'python3 app/service/segment_demo.py ' + message + ' ' + poke + ' ' + form_check + ' ' + path + ' &'
        os.system(command)
        return setting.SERVER_ADDRESS+"statics/" + poke + "/process.log"
        # except:
        #     return "503 wrong information"

    else:
        return "503 wrong information"

# 静态
@app.route('/formdetector', methods=['GET'])
def formdetector():
    if request.method == 'GET':
        if request.args.get('url'):
            message = request.args.get('url').replace("&", "\&")
            poke = str(int(time.time())) + str(random.randint(1, 10000))
            command = 'python3 app/service/form_demo.py ' + message + ' ' + poke + ' &'
            os.system(command)
        return setting.SERVER_ADDRESS+"statics/" + poke + "/process.log"

    else:
        return jsonify({'status':400}), 200, {
                'Content-Type': 'application/json;chaset=utf-8'}

@app.route('/statics/<path>/<string>', methods=['GET'])
def get_static_resource(path, string):
    if string.endswith("json"):
        return read_file_as_str("static/" + path + "/" + string), 200, {'Content-Type': 'application/json;chaset=utf-8'}
    elif string.endswith("png"):

        with open("static/" + path + "/"  + string, 'rb') as f:
            image = f.read()
        return Response(image, mimetype="image/png")
    else:
        return read_file_as_str("static/" + path + "/"  + string)

@app.route('/statics/<string>', methods=['GET'])
def get_static_resource_one(string):
    if string.endswith("json"):
        return read_file_as_str("static/" + string), 200, {'Content-Type': 'application/json;chaset=utf-8'}
    elif string.endswith("png"):
        with open("static/" + string, 'rb') as f:
            image = f.read()
        return Response(image, mimetype="image/png")
    else:
        return read_file_as_str("static/" + string)

class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(MyEncoder, self).default(obj)
