import sys
from form import Form
from lcypytools import common
import traceback
"""
TODO:细微结构差异要合并！！！
"""
if __name__ == "__main__":
    try: # 有命令行参数就使用命令行参数，不然就使用默认值
        poke = sys.argv[2]
        url = sys.argv[1]
    except:
        poke = "form_test1"
        url = "https://movie.douban.com/chart"

    folder_name = "static/"+ poke# 生成随机时间戳
    common.prepare_clean_dir(folder_name)  # 清空原有目录信息
    log = common.log(filename=folder_name + "/process.log")  # 打开log
    spliter = Form(log=log)
    try:
        # spliter.segment(url=sys.argv[1], output_folder=folder_name, is_output_images=False)
        spliter.segment(url=url, output_folder=folder_name, is_output_images=False)
        spliter.browser.quit()
    except Exception as err:
        traceback.print_exc()
        spliter.browser.quit()
        log.write_without_datetime("503 Procedure failed,please retry! Error is:"+str(err))
    exit(0)
    # folder_name = "data/weather"
    # folder_name = "data/ocean"
    # url_dir_list = ["http://www.weather.com.cn/weather/101280800.shtml","http://www.nmdis.org.cn/gongbao/",'http://www.nmdis.org.cn/ybfw/201301/t20130129_26027.html',"","http://service.cheosgrid.org:8076/APIMarket.html?id=1","http://service.cheosgrid.org:8076/detail.html?serviceId=46"]
    # folder_name_list = ["data/weather","data/ocean","data/oceaninfo","data/baidu",'data/gaofen',"data/PM25"]
    # url = "http://www.gov.cn/premier/lkq_wz.htm"
    # poke = str(int(time.time()))+str(random.randint(1,10000))
    # folder_name = "static/"+ poke# 生成随机时间戳


