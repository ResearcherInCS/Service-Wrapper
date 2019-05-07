## Configuration

`servicewrapper/BackEnd/app/service/setting.py` is the configuration file for the back-end code. Each of its parameters is explained as follows.

- `PORT` The port at which the back-end code runs.
- `PRODUCTION` The judgment condition of the Development Environment or the Production Environment，`False` means that the back-end code is running in the Development Environment，`True` means that the back-end code is running in the Production Environment.
- `SERVER_ADDRESS` The external access address and port of the server where the back-end code runs, for front-end access to files under `servicewrapper/static` folder.

### Production Environment

- `CHROME_BINARY_LOCATION_PRODUCTION`  The absolute address of a binary chrome start file. Install chrome inside the operating system where servicewrapper is running and find  out the address of its binary runtime file to fill in here.
- `DRIVER_PATH_PRODUCTION` The absolute address of  chrome driver.
- `HOST_PRODUCTION` The address at which the back-end code runs, running in docker as 0.0.0.0
- `MONGO_HOST_PRODUCTION` MongoDB database address, used to connect to the database, the default port is  27017, detail dataset configuration to see `servicewrapper/BackEnd/app/__init__.py`.
- `HOST_PRODUCTION_OUT_ADDRESS` The external access address and port of the server where the back-end code runs, for front-end access to files under `servicewrapper/static` folder. If reverse proxy is setted by nginx, please modify the corresponding files to ensure that the request `http://\$HOST_PRODUCTION\$:\$PORT\$/statics/.../[XXX.json|xxx.png]` can be mapped to corresponding API `http://xxxxx:yy/statics/.../[XXX.json|xxx.png]`. 

### Development Environment

- `CHROME_BINARY_LOCATION_LOCAL` The absolute address of a binary chrome start file in Development Environment。
- `DRIVER_PATH_PRODUCTION_LOCAL` Relative path to the chrome driver, the file shoule be  in `servicewrapper/BackEnd/app/service/driver`,Please select the appropriate chrome driver based on your OS and place it under this path.
- `HOST_LOCAL` The address at which the back-end code runs, by default, is `127.0.0.1` in the Development Environment。
- `MONGO_HOST_LOCAL` MongoDB database address, used to connect to the database, the default port is  27017, detail dataset configuration to see `servicewrapper/BackEnd/app/__init__.py`.



