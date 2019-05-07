$(function(){
	//工具方法
	var title = "";
	function getUrlParam(name) {
		var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)");
		var r = window.location.search.substr(1).match(reg);
		if(r != null) return unescape(decodeURI(r[2]));
		return "";
	}
	function getID() {
		var id = getUrlParam('id');
		var a = ""
		if(id == "0" || id == null || id == "")
			a =  "";
		else
			a =  "&category=" + id;
		console.log(a)
		return a
	}

	var Url = "http://localhost:8000/services";
    $.ajax({
        url: Url,
        type: "get",
        dataType: "json",
        success: function(data){
            $("#UL").empty();
            var pageData = data;
            var total = data.data;
            //渲染页面
            var str = "";
            var len = data.data.length;
            for(var k = 0; k < len; k++) {
                var imgSrc = "http://service.cheosgrid.org:8083/img/cb6fde35-fec7-4c57-94a5-8ddc17b15b55.png";
                var serviceName = total[k]["name"];
                var createTime = total[k]["create_time"];
                var serviceId = total[k]["api_id"];
                str += '<li  class="border-v1 pr" id="border-v1 fl "  data-item="'+ serviceId +'" >' +
                    '<a href="detail.html?serviceId='+ serviceId +'" onclick=setData(' + serviceId + ') target="_blank" style="text-decoration: none;">' +
                    '<img src="' + imgSrc + '"height="222px""  alt="图片" title="图片" />' +
                    '<h3 title="' + serviceName + '">' + serviceName + '</h3>' +
                    '<p class="createTime">'+ createTime +'</p>'+
                    '</a>' +
                    `<p>ID:${serviceId}</p>`
                '</li>'
            }
            $("#UL").html(str);
        }
    })
//最外面的括弧
})