//for index.html
import {server} from "./config.js"

$(document).ready(function () {
    let logUrl = ""
    let logTask
    let isStaticWrap = true
    console.log("11");
    function getUrlParam(name) {
        var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)")
        var r = window.location.search.substr(1).match(reg)
        if (r != null) return unescape(r[2])
        return ""
    }

    function staticWrap() {
        isStaticWrap = true
        let url = $("#url_text").val()
        $.get(server + "servicewrapper?url=" + url, function (result) {
            console.log("请求开始包装服务的结果", result)
            logUrl = result
            let time = 70
            logTask = setInterval(() => {
                $.get(logUrl)
                    .done((logResult) => {
                        time = time - 1
                        $("#logResult").html(logResult)
                        document.getElementById("logText").scrollTop = $("#logResult")[0].scrollHeight //始终保持日志滚动条在最下方
                        let logArray = logResult.split("\n")
                        logArray.pop()
                        if (logArray.length <= 1){
                            $("#logs").text("静态包装中： 爬取页面最长剩余时间：" + time + "s")
                            return;
                        }
                        else
                            $("#logs").text("静态包装中：请等待解析完毕")
                        let lastLine = logArray.pop()
                        console.log("lastLine", lastLine)
                        if (lastLine.startsWith("200")) {//分析结束
                            clearInterval(logTask)//停止请求日志
                            let jsonUrl = lastLine.split(" ").pop()
                            $.get(jsonUrl).done((result) => {//获取API信息
                                localStorage.setItem("api_info", JSON.stringify(result))
                                $("#nextBtn").css("display", "block")//显示下一步按钮
                                $("#logs").text("解析日志")

                            })
                        }
                        else if (lastLine.startsWith("503") || lastLine.startsWith("504") || (time <= 0 && logArray.length <= 1)) {
                            $("#logs").text("解析日志 包装失败，请重新点击按钮包装！")
                            clearInterval(logTask)
                        }
                    })
                    .fail((errorResult) => {
                        $("#logText").text("获取日志发生错误")
                        console.log("获取日志错误", errorResult)
                        $("#logs").text("解析日志失败，请重新包装")
                    })
            }, 1000)

        })
    }

    function dynamicWrap() {
        isStaticWrap = false
        console.log("click");
        let url = $("#url_text").val();
        $.get(server + "formdetector?url=" + url, function (result) {
            console.log("请求开始包装服务的结果", result)
            logUrl = result
            let time = 70
            logTask = setInterval(() => {
                $.get(logUrl)
                    .done((logResult) => {
                        time = time - 1
                        $("#logResult").html(logResult)
                        document.getElementById("logText").scrollTop = $("#logResult")[0].scrollHeight //始终保持日志滚动条在最下方
                        let logArray = logResult.split("\n")
                        logArray.pop()
                        if (logArray.length <= 1){
                            $("#logs").text("动态包装中： 爬取页面最长剩余时间：" + time + "s")
                            return;
                        }
                        $("#logs").text("动态包装中：请等待解析完毕")
                        let lastLine = logArray.pop()
                        console.log("lastLine", lastLine)
                        if (lastLine.startsWith("200")) {//分析结束
                            clearInterval(logTask)//停止请求日志
                            let strs = lastLine.split(" ")
                            let imgUrl = strs.pop()
                            let jsonUrl = strs.pop()
                            console.log("imgUrl", imgUrl)
                            console.log("jsonUrl", jsonUrl)
                            $.get(jsonUrl).done((result) => {//获取API信息
                                if (result.forms.length == 0) {
                                    $("#logs").text("未检测到表单，准备进行静态包装")
                                    staticWrap()
                                }
                                else {
                                    localStorage.setItem("form_info", JSON.stringify(result))
                                    localStorage.setItem("img_url", imgUrl)
                                    $("#nextBtn").css("display", "block")//显示下一步按钮
                                    $("#logs").text("解析日志")
                                }
                            })
                        }
                        else if (lastLine.startsWith("503") || lastLine.startsWith("504") || (time <= 0 && logArray.length <= 1)) {
                            $("#logs").text("解析日志 包装失败，请重新点击按钮包装！")
                            clearInterval(logTask)
                        }
                    })
                    .fail((errorResult) => {
                        $("#logText").text("获取日志发生错误")
                        console.log("获取日志错误", errorResult)
                        $("#logs").text("解析日志失败，请重新包装")
                    })
            }, 1000)

        }).fail(function(jqXHR, textStatus, errorThrown){
            console.log("错误",jqXHR,textStatus,errorThrown);
        })
    }

    if (getUrlParam("url") !== "" && getUrlParam("type") == "static") {
        $("#url_text").val(getUrlParam("url"))
        staticWrap()
        console.log("检测到url参数")
    }

    $("#staticWrap").click(staticWrap)
    $("#dynamicWrap").click(dynamicWrap)
    $("#nextBtn").click(() => {
        console.log("testBtn2 clicked")
        if (isStaticWrap)
            window.location.href = "mainTextSelect.html"
        else
            window.location.href = "formSelect.html"
    })
})