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

from form import Form
from lcypytools import common
import traceback
import sys
"""
TODO:细微结构差异要合并！！！
"""
if __name__ == "__main__":
    try: # 有命令行参数就使用命令行参数，不然就使用默认值
        poke = sys.argv[2]
        url = sys.argv[1]
    except:
        poke = "form_test1"
        url = "http://gujia.mlr.gov.cn/JGPublish/Publish/Index"

    folder_name = "static/"+ poke# 生成随机时间戳
    common.prepare_clean_dir(folder_name)  # 清空原有目录信息
    log = common.log(filename=folder_name + "/process.log")  # 打开log
    spliter = Form(log=log)
    try:
        # spliter.segment(url=sys.argv[1], output_folder=folder_name, is_output_images=False)
        spliter.segment(url=url, output_folder=folder_name, is_output_images=False)
        spliter.browser.quit()
    except:
        traceback.print_exc()
        spliter.browser.quit()
        log.write_without_datetime("503 Procedure failed,please retry!")
    exit(0)
    # folder_name = "data/weather"
    # folder_name = "data/ocean"
    # url_dir_list = ["http://www.weather.com.cn/weather/101280800.shtml","http://www.nmdis.org.cn/gongbao/",'http://www.nmdis.org.cn/ybfw/201301/t20130129_26027.html',"","http://service.cheosgrid.org:8076/APIMarket.html?id=1","http://service.cheosgrid.org:8076/detail.html?serviceId=46"]
    # folder_name_list = ["data/weather","data/ocean","data/oceaninfo","data/baidu",'data/gaofen',"data/PM25"]
    # url = "http://www.gov.cn/premier/lkq_wz.htm"
    # poke = str(int(time.time()))+str(random.randint(1,10000))
    # folder_name = "static/"+ poke# 生成随机时间戳
