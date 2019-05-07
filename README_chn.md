## Service Wrapper

- [English](README.md)

## 什么是Service Wrapper

**Service Wrapper**是一种基于[网页分割算法](https://github.com/liaocyintl/WebSegment)的网页数据提取封装系统。该系统仅需用户少量点击即可得到网页中的**核心元数据的位置描述信息**，将HTML文档转换为结构化数据，封装成服务，并提供可直接调用的**RESTFul API接口**。

**Service Wrapper**通过**服务提取**和**服务调用**两个模块来实现系统的后台功能，并提供了一系列简单的**前端操作界面**以辅助用户完整地实现整个操作流程。**服务提取模块**面向**服务包装者**，该模块利用**爬虫工具和网页分割技术**得到网页核心数据位置，并根据数据在网页中的结构生成网页分割规则， 存储在数据库中。**服务调用模块**面向**服务调用者**，该模块为每个服务提供 RESTFul API  的描述信息和调用方法，服务调用者正确调用后，该模块返回结构化的数据。 同时，该系统提供了包含服务提取、服务调用和服务信息展示的一系列前端操作页面，供用户可以方便地使用之。

![arch](introduction_image/arch.png)



## 技术架构

![nginx](introduction_image/nginx.png)

系统采用了`前后端分离`的开发模式，可分为前端和后端两部分。

前端部分，本系统采用原生HTML、CSS和JS 实现，后端API基于`flask`实现。

后端部分，本系统提供了两种环境下运行方式：`本地环境`和`生产环境`。在生产环境下，采用了`nginx+docker compose`的部署方式，以`gunicorn`作为flask的Python WSGI UNIX HTTP服务器。

后端技术栈包含：

- `flask`
- `chrome driver`
- `selenium`
- `mongodb`
- `nginx`
- `docker-compose`
- `gunicorn`

## 配置

- [后端配置](BackEnd/README_chn.md)
- [前端配置](FrontEnd/README.md)

## 快速开始

Service Wrapper系统已经在`Linux`、`MacOS`和`windows`等多个系统上测试过，所以您可以将之运行在不同的操作系统或者云端服务器上。

Service Wrapper 采用`前后端分离`的系统架构，文件夹 `BackEnd` 为系统后端代码, 文件夹 `FrontEnd` 是前端代码。

我们针对本地环境和生产环境，提供了两份不同的配置。为方便您快速开始，我们将分别针对两个配置分别介绍。

### 下载

```git clone https://github.com/ResearcherInCS/Service-Wrapper.git```

### 本地环境

本地环境运行需要python版本 `python-3.6`及以上，且需要系统已安装[mongodb](https://www.mongodb.com/download-center/community)，已启动mongodb服务。

```shell
# conda创建虚拟环境
conda create -n service-wrapper python=3.6

# 启动虚拟环境
source activate service-wrapper
```

本地运行后端代码：

请先根据您的操作系统选择合适的[chrome driver](http://chromedriver.storage.googleapis.com/index.html)，并放置在文件夹下`servicewrapper/BackEnd/app/service/driver`

```shell
cd servicewrapper/BackEnd
# 下载必须的库
pip install -r requirement.txt

# 运行方式1：通过python直接运行
python run.py
# 运行方式2（推荐）：利用gunicorn作为HTTP server 运行
gunicorn -w 4 -b :8000 run:app false
```

本地运行前端代码:

```shell
cd servicewrapper/FrontEnd

# 通过http-server运行
http-server --cors  ./ index.html  # index.html is the start page

```

### 生产环境

您可以在`已下载Docker 1.11+ 和 Docker compose`的操作系统中运行Service Wrapper。

```shell
cd servicewrapper/BackEnd/docker

sudo docker-compose build
sudo docker-compose up -d
```

因为生产环境是利用 [nginx](https://www.nginx.com/) 作为静态资源服务器和反向代理服务器，所以为了适配您的生产环境，您需要针对性地修改`servicewrapper/BackEnd/docker/nginx.conf`中的相关字段。



## 使用手册

Service Wrapper适用于网页结构清晰，核心数据的布局方式大致是一致的网页。

Service Wrapper将封装的网页分为`静态网页`和`动态网页`， 其中静态网页为打开网页时数据已经呈现在页面中的网页，如[中国地震台网-快捷查询](http://www.ceic.ac.cn/speedsearch?time=7)；动态网页为需要手动填写一定筛选条件后，点击查询按钮才会出现服务数据的网页，如[中国地震台网-历史查询](http://www.ceic.ac.cn/history)。

两种网页的封装步骤有所差异，其中动态网页比静态网页多了一个筛选条件填写的步骤，因此接下来将通过动态网页封装的例子来演示如何使用本系统。

- 第一步，打开起始网页--网页分析，在`Input 1`中输入`需要封装的网页的网址`, 点击`Click 1`。在解析日志窗口可看到解析日志`Extraction Log 1`，当出现`Click 2`按钮后，点击可进入至下一网页—表单选择。

![step1](introduction_image/step1.png)



- 第二步，在网页—表单选择中，根据”表单分块图“在`Select 1`中选择对应的表单编号，下侧的”自定义输入参数“会随之更改。在`Input 2`中输入或者更改参数名称、输入示例值和描述信息；在`Select 2`中选择输入参数后确定的按钮。（需要注意的是，在Input 2中输入的输入示例值，系统后台将自动将之填入对应区域，并点击`Select 2`中选择的按钮，进行获取数据。） 点击`Click 3`将对网页进行服务提取，可以在`Extraction 2`中看到解析日志。当出现`Click 4`按钮后，点击可进入至下一网页—正文及结果项选择。

![step2](introduction_image/step2.png)

- 第三步，在网页—正文及结果项选择中，根据”网页分块图“在`Select 3`中选择对应的表单编号，下侧的网页块中的文本信息会随之更改。在选择完成后，点击`Click 5`进入下一网页--包装。

![step3](introduction_image/step3.png)

- 第四步，在网页—包装中，可以在`Input 3`中看到API的基本信息和所提取到的数据默认信息，可以根据实际情况在`Input 3`中进行修改。修改完成后，点击`Click 6`即完成了服务包装工作。下一步，会进入服务调用示例网页--测试。

![step4](introduction_image/step4.png)

- 第五步，在完成服务提取后，服务包装者需要通过测试来查看服务提取的结果是否正确，参数是否成功。在测试页面中，”最大页数“参数是一个超参数，独立于服务之外，表示此次获取数据会提取网页中的多少页内的数据，默认最高为5页。”输入参数“为步骤二所填写的参数，指将以这些参数作为条件进行数据查询；”筛选参数“为步骤四所填写的参数，指获取到的所有数据将根据此处的参数做一次筛选，只返回满足该参数条件的数据。

![step5](introduction_image/step5.png)



静态网页和动态网页的操作步骤基本一致，只是缺少的步骤二，即静态网页包装由上述步骤一，步骤三，步骤四和步骤五组成。