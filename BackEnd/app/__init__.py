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


from flask import Flask
from flask_mongoengine import MongoEngine
import logging
from app.service import setting

app = Flask(__name__)
# app.config.update(RESTFUL_JSON=dict(ensure_ascii=False))
handler = logging.FileHandler('flask-debug.log', encoding='UTF-8')

handler.setLevel(logging.DEBUG)

logging_format = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)s - %(message)s')

handler.setFormatter(logging_format)

app.logger.addHandler(handler)

host = ""
if setting.PRODUCTION:
    host = setting.MONGO_HOST_PRODUCTION
else:
    host = setting.MONGO_HOST_LOCAL

print(host)
app.config['MONGODB_SETTINGS'] = {
    'db':   'flask_web',
    'host': host,  ##upload 修改
    'port': 27017
}
app.config['JSON_AS_ASCII'] = False

db = MongoEngine(app)

from app import controllers

