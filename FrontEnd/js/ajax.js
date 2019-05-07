$(function() {
	function getUrlParam(name) {
		var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)");
		var r = window.location.search.substr(1).match(reg);
		if(r != null) return unescape(r[2]);
		return null;
	}
    function formatXml(xml) {
        var formatted = '';
        var reg = /(>)(<)(\/*)/g;
        xml = xml.replace(reg, '$1\r\n$2$3');
        var pad = 0;
        jQuery.each(xml.split('\r\n'), function(index, node) {
            var indent = 0;
            if (node.match( /.+<\/\w[^>]*>$/ )) {
                indent = 0;
            } else if (node.match( /^<\/\w/ )) {
                if (pad != 0) {
                    pad -= 1;
                }
            } else if (node.match( /^<\w([^>]*[^\/])?>.*$/ )) {
                indent = 1;
            } else {
                indent = 0;
            }

            var padding = '';
            for (var i = 0; i < pad; i++) {
                padding += '  ';
            }

            formatted += padding + node + '\r\n';
            pad += indent;
        });

        return formatted;
    }
    //接口URL
	var ApiUrl = "http://localhost:8000/services";
	var serviceId = getUrlParam("serviceId");
	var urlAdress = ApiUrl + '/' + serviceId;
	var detailList = {
		getData: function() {
			//发起请求
			$.ajax({
				type: "get",
				url: urlAdress,
				dataType: "json",
				success: function(data) {
					data = data.data;
					var status = 0;
					var str = "";
					var str1 = "";
					var optionUl = $("#optionUl");
					// getTitle
					if(status == 0) {
						var imgInfo = "http://service.cheosgrid.org:8083/img/cb6fde35-fec7-4c57-94a5-8ddc17b15b55.png";
						$("#detail-img").attr("src", imgInfo);
						$("#title").text(data.name);
                        $("#sname").val(data.name);
                        $("#serviceId").val(serviceId);
						$("#serviceName").text(data.name);
						$("#service-title").text(data.name);
						$("#introduction").text(data.api_introduction);
						$("#service-intro").text(data.api_introduction);
							//加载侧栏选项
							var optionName = data["name"];
							str += '<li class="navi-item pr">' +
								'<h5 class="navi-title text-overflow-fix" data-service-menu="'  + '"  data-api-menu="'  + '" id="IPC" title="' + optionName + '">' + optionName + '</h5>' +
								'<i></i>' +
								'</li>'
							optionUl.html(str);
							//加载页面内容
							$(".navi-item:first").addClass("active");
							$("#detail-img").attr("alt", data.serviceName);
							var itemsWrapper = $(".interface-item")
							var desc = data["api_introduction"];
							var address = data["api_address"];
							var way = data["api_call_way"];
							var callExample = data["call_example"];
							var example = data["api_address"];
							var outPutExample = data["result"];
							if(data['return_style'] == "JSON"){
								try
								{
                                    outPutExample = JSON.stringify(JSON.parse(data["result"]), null, 24);
								}
								catch (e)
								{
								}
							}
							else if(data['return_style'] == "XML")//显示XML
                            	outPutExample = `${formatXml(outputExample).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/ /g, '&nbsp;').replace(/\n/g,'<br />')}`;
							// console.log(outPutExample);
							//拼接主体结构
							str1 += '<div class="interface-detail db clearfix" data-api-detail="'  + '">' +
								'<div class="interface-line clearfix">' +
								'<span class="api-content-left title" style="color: #333; font-size:16px; font-Weight: 600;width: 100% " >' + optionName + '</span>' +
								'</div>' +
								'<p class="interface-line clearfix">' +
								'<span class="api-content-left title">接口描述 :</span>' +
								'<span id="desc" class="api-content-right" data-api-link="3653">' + desc + '</span></p>' +
								'<p class="interface-line clearfix">' +
								'<span class="api-content-left title">接口地址 :</span>' +
								'<span id="address" class="api-content-right" data-api-link="3653">' + address + '</span></p>' +
								'<p class="interface-line clearfix">' +
								'<span class="api-content-left title">请求方法 :</span>' +
								'<span id="way" class="api-content-right" data-api-req-method="3653">' + way + '</span>' +
								'</p>' +
								'<p class="interface-line clearfix">' +
								'<span class="api-content-left title">请求示例 :</span>' +
								'<span id="example" class="api-content-right" data-api-req-method="3653">' + callExample + '</span>' +
								'</p>' +
								'<div class="interface-line clearfix">' +
								'<span class="api-content-left title" style = "font-size: 17px;font-weight:600">请求参数 :</span>' +
								'</div>' +
								'<div class="interface-line clearfix">' +
								'<table>' +
								'<thead>' +
								'<tr>' +
								'<th class="td-1">名称</th>' +
								'<th class="td-2">类型</th>' +
								'<th class="td-3">必填</th>' +
								'<th class="td-1">示例值</th>' +
								'<th class="td-5">描述</th>' +
								'</tr>' +
								'</thead>' +
								'<tbody id="yytbody'  + '" data-api-param="'  + '"></tbody>' +
								'</table>' +
								'</div>'+
								'<div class="interface-line clearfix">' +
								'<span class="api-content-left title" style = "font-size: 17px;font-weight:600">返回参数 :</span>' +
								'</div>' +
								'<div class="interface-line clearfix">' +
								'<span class="api-content-left title">系统级返回参数 :</span>' +
								'</div>' +
								'<div class="interface-line clearfix">' +
								'<table>' +
								'<thead>' +
								'<tr>' +
								'<th class="td-1">名称</th>' +
								'<th class="td-2">类型</th>' +
								'<th class="td-4">示例值</th>' +
								'<th class="td-5">描述</th>' +
								'</tr>' +
								'</thead>' +
								'<tbody id="fhtbody1' + '" data-api-param="' + '"></tbody>' +
								'</table>' +
								'</div>' +
								'<div class="interface-line clearfix">' +
								'<span class="api-content-left title">应用级返回参数 :</span>' +
								'</div>' +
								'<div class="interface-line clearfix">' +
								'<table>' +
								'<thead>' +
								'<tr>' +
								'<th class="td-1">名称</th>' +
								'<th class="td-2">类型</th>' +
								'<th class="td-4">示例值</th>' +
								'<th class="td-5">描述</th>' +
								'</tr>' +
								'</thead>' +
								'<tbody id="fhtbody2'  + '" data-api-param="'  + '"></tbody>' +
								'</table>' +
								'</div>' +
								'<div class="interface-line clearfix clearfix">' +
								'<span class="api-content-left title">返回示例 :</span>' +
								'<div class="api-content-right'  + '"><pre>' + outPutExample + '</pre></div>' +
								'</div>' +
								'</div>'

							itemsWrapper.html(str1);
							$(".interface-detail:first").siblings().css("display", "none");

						//点击动态加载过来的展示不同的结果
						$(".navi-item").on("click", function() {
							$(".navi-item").removeClass("active");
							$(this).addClass("active");
							var tid2 = $(this).find(".navi-title").attr("data-service-menu");
							var tid3 = $(this).find(".navi-title").attr("data-api-menu");
							$(".interface-detail").hide();
							$(".interface-detail[data-service-detail='" + tid2 + "']").show();
							$(".interface-detail[data-api-detail='" + tid3 + "']").show();
						})
							
					} else {
						$("#optionUl").html("");
						$(".interface-detail").html("");
					}
                    // 请求参数
                    if(status == 0) {
                            var json = data;
                            var str = ("str" );
                            var jsonObj =$.parseJSON(json.arguments);
                            for(var j = 0; j < jsonObj.length; j++) {
                                var paraName = jsonObj[j]["名称"];
                                var paraType = jsonObj[j]["类型"];
                                var required = jsonObj[j]["必填"];
                                var exampleValue = jsonObj[j]["示例值"];
                                var description = jsonObj[j]["描述"];
                                str += '<tr id="tr">' +
                                    '<td class="td-1" data-param-name>' + paraName + '</td>' +
                                    '<td class="td-2">' + paraType + '</td>' +
                                    '<td class="td-3">' + required + '</td>' +
                                    '<td class="td-5 pr">' +
                                    '' + exampleValue + '' +
                                    '</td>' +
                                    '<td class="td-1 api-param-ellipsis" >' +
                                    '' + description + '' +
                                    '</td>' +
                                    '</tr>'
                            }
                            $("#yytbody" ).html(str);
                            if(jsonObj.length<=0)
                                $("#yytbody" ).html("<tr><td>暂无</td><td>暂无</td><td>暂无</td><td>暂无</td><td>暂无</td></tr>");
                    }




                    // 系统级别返回参数
                    if(status == 0) {
                            var str = '<tr><td>status</td><td class="td-2">int</td><td class="td-4">10000</td><td class="td-5 pr">返回的状态码</td></tr><tr><td>msg</td><td class="td-2">string</td><td class="td-4">请求成功</td><td class="td-5 pr">返回的结果信息</td><tr><td>data</td><td class="td-2">json</td><td class="td-4">null</td><td class="td-5 pr">返回的实际数据</td></tr></tr>'
                            $("#fhtbody1").html(str);
                    }
					// 应用级别返回参数
                    if(status === 0) {
						var str = "";
						var jsonObj = $.parseJSON(data.result_arguments);
						for(var j = 0; j < jsonObj.length; j++) {
							var paraName = jsonObj[j]["名称"];
							var paraType = jsonObj[j]["类型"];
							var exampleValue = jsonObj[j]["示例值"];
							var description = jsonObj[j]["描述"];
							str += '<tr>' +
								'<td class="td-1" data-param-name>' + paraName + '</td>' +
								'<td class="td-2">' + paraType + '</td>' +
								'<td class="td-4">' + exampleValue + '</td>' +
								'<td class="td-5 pr">' +
								''+ description +''
							'</td>' +
							'</tr>';
						}
						$("#fhtbody2" ).html(str);
						if(jsonObj.length<=0)
							$("#fhtbody2" ).html("<tr><td>暂无</td><td>暂无</td><td>暂无</td><td>暂无</td></tr>");
                    }
                    //错误码
                    if(status == 0) {
                        var list = $.parseJSON(data.error_code);
                        var str = '';
                        for(var i = 0; i < list.length; i++) {
                            var code = list[i]["错误码"];
                            var desc = list[i]["说明"];
                            str += '<tr>' +
                                '<td class="record-col-15">' + code + '</td>' +
                                '<td class="record-col-45">' + desc + '</td>' +
                                '</tr>'
                        }
                        $("#errorBoddy").html(str);
                        if(list.length<=0)
                            $("#errorBoddy").html(`<tr><td class="record-col-15">暂无</td><td>暂无</td></tr> `);
                    }
				}
			})
		},

	}
	detailList.getData();
})