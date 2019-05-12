# -*- coding: utf-8 -*-
import json
import re
import urllib

"""
根据字段内容分析字段类型的类
先分析是否为int，再分析是否为float，如果不是，就送到知识图谱中进行分析，如果能分析出来就按照图谱内容返回，否则返回text
"""


class typeAnalyse:
    def __init__(self,str="",auxiliary=""):
        self.type = "text" # 默认为text类型
        self.str = str
        self.auxiliary = auxiliary
        # print("text:",self.str)

    def getType(self):
        try:
            t = int(self.str)
            self.type = "integer" + self.auxiliary
        except:
            try:
                t = float(self.str)
                self.type = "float"+ self.auxiliary
            except:
                self.kgAnaylse()
        return self.type

    def getJsonFromWeb(self,website=""):
        return json.loads(urllib.request.urlopen(website, data=None, timeout=10).read().decode("utf-8"))


    def kgAnaylse(self):
        website = 'http://shuyantech.com/api/entitylinking/cutsegment?q='+urllib.parse.quote(self.str)+'&apikey=a8b2f0ea73690d84daaaec3cf627f6b4'
        t = self.getJsonFromWeb(website)
        # print(t)
        if len(t["entities"]) == 0:
            return
        else:
            e = t["entities"][0][1]
            # print(t["entities"])
            stre = re.compile('（.*）')
            e = re.sub(stre,"",e) # 删掉括号以及所有带括号的内容
            website = 'http://shuyantech.com/api/cnprobase/concept?q=' + urllib.parse.quote(
                e) + '&apikey=a8b2f0ea73690d84daaaec3cf627f6b4'
            # print(website)
            t = self.getJsonFromWeb(website)
            if len(t["ret"]) != 0:
                self.type = t["ret"][0][0] + self.auxiliary

        # http://shuyantech.com/api/entitylinking/cutsegment?q=
        # http://shuyantech.com/api/cnprobase/concept?q=

if __name__ == '__main__':
    print(typeAnalyse("刘德华").getType())