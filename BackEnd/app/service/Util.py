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

import os
def shutdown_crawl(crawl):
    try:
        if crawl:
            crawl._end()  # 关闭chromedriver
            del crawl
    except:
        pass


def read_file_as_str(file_path):
    # 判断路径文件存在
    if not os.path.isfile(file_path):
        return "404"
    all_the_text = open(file_path).read()
    # print type(all_the_text)
    return all_the_text

