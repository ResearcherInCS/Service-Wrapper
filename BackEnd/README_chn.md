## 配置/Configuration

`servicewrapper/BackEnd/app/service/setting.py`为后端代码的配置文件。其每一项解释如下：

- `PORT`后端代码运行时的端口，默认为8000
- `PRODUCTION` 本地环境或者是生产环境的判断条件，`False`表示后端代码运行在本地环境下，`True`表示后端代码运行在生产环境下。
- `SERVER_ADDRESS` 后端代码运行的服务器的对外访问地址, 用以前端访问`servicewrapper/static`文件夹下的文件。

### 生产环境 / Production Environment

- `CHROME_BINARY_LOCATION_PRODUCTION`  二进制 chrome 文件的绝对地址。请在servicewrapper运行的操作系统中安装chrome，并找出其二进制运行文件的地址填于此处。
- `DRIVER_PATH_PRODUCTION` chrome driver文件的绝对地址。
- `HOST_PRODUCTION` 后端代码运行时的地址，在docker中为`0.0.0.0`。
- `MONGO_HOST_PRODUCTION` MongoDB数据库的地址，用以连接数据库，端口为默认的27017，配置见`servicewrapper/BackEnd/app/__init__.py`。
- `HOST_PRODUCTION_OUT_ADDRESS` 后端代码运行的服务器的对外访问端口, 用以前端访问`servicewrapper/static`文件夹下的文件，此时如果通过nginx配置，请注意修改对应文件以确保请求`http://\$HOST_PRODUCTION\$:\$PORT\$/statics/[XXX.json|xxx.png]`能够映射到flask的对应API下。 

### 本地环境 / Development Environment

- `CHROME_BINARY_LOCATION_LOCAL` 本地环境下二进制 chrome 文件的绝对地址。
- `DRIVER_PATH_PRODUCTION_LOCAL` 本地环境下chrome driver文件的相对路径地址，该文件在`servicewrapper/BackEnd/app/service/driver`下，请根据本地系统选择合适的chrome driver，并置于该路径下。
- `HOST_LOCAL` 代码运行时的地址，本地环境下默认为`127.0.0.1`。
- `MONGO_HOST_LOCAL` MongoDB数据库的地址，用以连接数据库，端口为默认的27017，配置见`servicewrapper/BackEnd/app/__init__.py`。



