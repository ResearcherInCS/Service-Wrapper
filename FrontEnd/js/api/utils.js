//前端传参不同页面之间利用webStorage共享 
var storage = window.sessionStorage;
function setData(serviceId) {
	storage.setItem("serviceId", serviceId);
}
function getData() {
	return storage.getItem("serviceId");
}
function setName(serviceName) {
	storage.setItem("serviceName", serviceName);
}
function getName() {
	return storage.getItem("serviceName");
}

//参数拼接 貌似用不上
var Common = {
	utils: {
		// 将数据对象转换成url 的形式，例如入参为[{a:'b'},{c:'d'}] 出参则为 a=b&c=d
		danymicUrlArguments: function(args) {
			var UrlArguments = "";
			if(!args || 0 == args.length)
				return UrlArguments;
			if(!args instanceof Array) {
				for(var index in args) {
					var arg = args[index];
					UrlArguments = UrlArguments + Common.utils.joinObject(arg);
				}
			} else if(typeof args == 'object') {
				UrlArguments = UrlArguments + Common.utils.joinObject(args);
			} else {
				return UrlArguments;
			}
			if(UrlArguments) {
				return UrlArguments.substring(0, UrlArguments.length - 1);
			}
			return UrlArguments;
		},
		joinObject: function(arg) {
			var UrlArguments = "";
			if(arg && typeof arg == 'object') {
				for(var p in arg) {
					if(p && arg[p] && typeof p == "string" &&
						typeof arg[p] == "string") {
						UrlArguments = UrlArguments + p + "=" + arg[p] + "&";
					}
				}
			}
			return UrlArguments;
		},
		// 将Url 与Url 参数连接起来
		getFullUrl: function(Url, UrlArguments) {
			if(!Url)
				return "";
			var calcUrlArgs = Common.utils.danymicUrlArguments(UrlArguments);
			if(!calcUrlArgs)
				return Url;
			var lastIndexOfP = Url.lastIndexOf("?");
			if(lastIndexOfP == -1)
				return Url + "?" + calcUrlArgs;
			if(lastIndexOfP == Url.length - 1)
				return Url + calcUrlArgs;
			var lastIndexOfA = Url.lastIndexOf("&");
			if(lastIndexOfA == Url.length - 1)
				return Url + calcUrlArgs;
			return Url + "&" + calcUrlArgs;
		},
		// 增加时间后缀
		getFullUrlTime: function(Url, UrlArguments) {
			var calcFullUrl = Common.utils.getFullUrl(Url, UrlArguments);
			if(!calcFullUrl)
				return "";
			return Common.utils.getFullUrl(calcFullUrl, [{
				t: new Date().getTime().toString()
			}]);
		},
		// 给URL增加时间后缀
		getTimeUrl: function(Url) {
			return Common.utils.getFullUrlTime(Url, null);
		},
		// post 方式访问后台地址
		goLocation: function(Url, UrlArguments) {
			var calcFullUrl = Common.utils.getFullUrlTime(Url, UrlArguments);
			if(!calcFullUrl)
				throw new Error("the URL has problem");
			location = calcFullUrl;
		},
		// get 方式访问后台地址
		goLocationUrl: function(Url) {
			return Common.utils.goLocation(Url, null);
		},
		// open 访问后台地址
		open: function(Url, UrlArguments) {
			var calcFullUrl = Common.utils.getFullUrlTime(Url, UrlArguments);
			if(!calcFullUrl)
				throw new Error("the URL is has problem");
			open(calcFullUrl, "_blank");
		},
		// 重复提交
		disInputResubmit: function(object, fn) {
			jQuery(object).attr("disabled", "disabled").val("提交中...");
			fn();
		},
		// 删除form空值
		getFormData: function(jQForm) {
			var obj = jQForm.serializeArray();
			jQuery(obj).each(function(i, field) {
				if(!field.value) {
					delete field.name;
				}
			});
			return obj;
		}
	}
};