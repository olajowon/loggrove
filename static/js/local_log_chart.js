/**
 * Created by zhouwang on 2018/6/24.
 */


function show_24h_chart(_this){
    /* 24 小时实时图表 */

    if(interval){
        window.clearInterval(interval)
    }

    var form_obj = $(_this).parent().parent().parent()
    form_obj.prev().empty()
    $(".error_text").empty()
    $("#log_chart").parent().show()
    var local_log_file_id = form_obj.find("[name=local_log_file_id]").val()
    var local_log_file_path = form_obj.find("[name=local_log_file_id]").find("option:selected").text()
    var monitor_item_ids = form_obj.find("[name=monitor_item_id]").val()
    var get_data = "local_log_file_id=" + local_log_file_id + "&monitor_item_id=" + monitor_item_ids.join("&monitor_item_id=")

    $.ajax({
        url:"/local_log/chart/",
        type:"GET",
        data:get_data,
        success:function(result){
            var response_data = jQuery.parseJSON(result)
            var data = response_data["data"]

            var chartdata = {
                "title": {"text": "24小时日志行数趋势图"},
                "subtitle": {"text": local_log_file_path},
                "series": data[0]["series"],
                "xAxis": data[0]["xAxis"]
            }

            write_interval_chart(chartdata) // 画图

            interval = window.setInterval("update_24h_chart('"+get_data+"')", 30000);   // 动态刷新
        },
        error:function(result){
            if (result.status != 0) {
                var response_data = jQuery.parseJSON(result.responseText)
                if (response_data["code"] == 400) {
                    for (var k in response_data["error"]) {
                        form_obj.find("[name='" + k + "_error']").text(response_data["error"][k])
                    }
                }else{
                    form_obj.prev().html(
                        '<div class="alert alert-danger">' +
                        '<i class="fa fa-times"></i> ' + response_data["msg"] +
                        '</div>'
                    )
                }
            }else{
                form_obj.prev().html(
                    '<div class="alert alert-danger">' +
                    '<i class="fa fa-times"></i> HTTP: 0 ' + result.statusText +
                    '</div>'
                )
            }
        }
    })
}


function open_chart_modal(local_log_file_id){
    /* 图表modal */

    if(interval){
        window.clearInterval(interval)
    }

    $("#update_chart").empty()

    $("#chartModal").modal("show")
    var get_data = "local_log_file_id=" + local_log_file_id
    $.ajax({
        url:"/local_log/chart/",
        type:"GET",
        data:get_data,
        success:function(result){
            var response_data = jQuery.parseJSON(result)
            var data = response_data["data"]
            var tr = $("#tr"+local_log_file_id)

            var chartdata = {
                "title": {"text": "24小时日志行数趋势图"},
                "subtitle": {"text": tr.children("td:eq(0)").text()},
                "series": data[0]["series"],
                "xAxis": data[0]["xAxis"],
            }

            write_interval_chart(chartdata)

            interval = window.setInterval("update_24h_chart('"+ get_data +"')", 30000);

            $('#chartModal').on('hide.bs.modal',
                function() {
                    window.clearInterval(interval)
                }
            )
        },
        error:function(result){
            if (result.status != 0) {
                var response_data = jQuery.parseJSON(result.responseText)
                $("#update_chart").html(
                    '<div class="alert alert-danger">' +
                    '<i class="fa fa-times"></i> ' + response_data["msg"] +
                    '</div>'
                )
            }else{
                $("#update_chart").html(
                    '<div class="alert alert-danger">' +
                    '<i class="fa fa-times"></i> HTTP: 0 ' + result.statusText +
                    '</div>'
                )
            }
        }
    })
}


function update_24h_chart(get_data){
    /* 实时刷新 */

    $.ajax({
        url:"/local_log/chart/",
        type:"GET",
        data:get_data,
        success:function(result){
            var response_data = jQuery.parseJSON(result)
            var data = response_data["data"]
            chartobj.xAxis[0].update({"min":data[0]["xAxis"]["min"], "max":data[0]["xAxis"]["max"]})
            chartobj.update({
                "series":data[0]["series"]
            })
        },
        error:function(result){}
    })
}


function show_interval_chart(_this){
    /* 连续查询图表 */
    if(interval){
        window.clearInterval(interval)
    }

    var form_obj = $(_this).parent().parent().parent()
    form_obj.prev().empty()
    $(".error_text").empty()
    $("#log_chart").parent().show()
    var local_log_file_id = form_obj.find("[name=local_log_file_id]").val()
    var local_log_file_path = form_obj.find("[name=local_log_file_id]").find("option:selected").text()
    var begin_time = form_obj.find("[name=begin_time]").val()
    var end_time = form_obj.find("[name=end_time]").val()
    var monitor_item_ids = form_obj.find("[name=monitor_item_id]").val()
    var get_data = "local_log_file_id=" + local_log_file_id + "&monitor_item_id=" + monitor_item_ids.join("&monitor_item_id=") +
        "&begin_time=" + begin_time + "&end_time=" + end_time

    $.ajax({
        url:"/local_log/chart/",
        type:"GET",
        data: get_data,
        success:function(result){
            var response_data = jQuery.parseJSON(result)
            var data = response_data["data"]
            var chartdata = {
                "title": {"text": "日志行数趋势图"},
                "subtitle": {"text": local_log_file_path},
                "series": data[0]["series"],
                "xAxis": data[0]["xAxis"]
            }

            write_interval_chart(chartdata)
        },
        error:function(result){
            if (result.status != 0) {
                var response_data = jQuery.parseJSON(result.responseText)
                if (response_data["code"] == 400) {
                    for (var k in response_data["error"]) {
                        form_obj.find("[name='" + k + "_error']").text(response_data["error"][k])
                    }
                }else{
                    form_obj.prev().html(
                        '<div class="alert alert-danger">' +
                        '<i class="fa fa-times"></i> ' + response_data["msg"] +
                        '</div>'
                    )
                }
            }else{
                form_obj.prev().html(
                    '<div class="alert alert-danger">' +
                    '<i class="fa fa-times"></i> HTTP: 0 ' + result.statusText +
                    '</div>'
                )
            }
        }
    })
}


function show_contrast_chart(_this){
    /* 日期对比查询 */
    if(interval){
        window.clearInterval(interval)
    }

    var form_obj = $(_this).parent().parent().parent()
    form_obj.prev().empty()
    $(".error_text").empty()
    $("#log_chart").parent().show()
    var local_log_file_id = form_obj.find("[name=local_log_file_id]").val()
    var local_log_file_path = form_obj.find("[name=local_log_file_id]").find("option:selected").text()
    var monitor_item_ids = form_obj.find("[name=monitor_item_id]").val()
    var dates = [form_obj.find("[name=date]").eq(0).val(), form_obj.find("[name=date]").eq(1).val()]

    var get_data = "local_log_file_id=" + local_log_file_id + "&date=" + dates.join("&date=") + "&mode=contrast" +
        "&monitor_item_id=" + monitor_item_ids.join("&monitor_item_id=")
    $.ajax({
            url:"/local_log/chart/",
            type:"GET",
            data: get_data,
            success:function(result){
                var response_data = jQuery.parseJSON(result)
                var data = response_data["data"]

                Highcharts.chart('log_chart', {
                    chart: {
                        type: 'spline',
                        zoomType: 'x'
                    },
                    title: {"text": "日志行数对比图"},
                    subtitle: {"text": local_log_file_path},
                    xAxis: {
                        type: 'datetime',
                        title: {
                            text: null
                        },
                        min: data[0]["xAxis"]["min"],
                        max: data[0]["xAxis"]["max"],
                        labels: {
                            formatter:function () {
                                return Highcharts.dateFormat("%H:%M",this.value);
                            },
                        }
                    },
                    yAxis: {
                        title: {
                            text: '行数'
                        },
                        min: 0
                    },
                    tooltip: {
                        valueSuffix: '',
                        shared: true,
                        crosshairs: true,

                        dateTimeLabelFormats: {
                            minute:"%H:%M",
                        },
                    },
                    plotOptions: {
                        spline: {
                            marker: {
                                enabled: true
                            }
                        }

                    },
                    series: data[0]["series"],
                    credits: {
                        text: 'Loggrove',
                        href: ''
                    },
                    global: {
                        useUTC: false
                    }
                });
            },
            error:function(result){
                if (result.status != 0) {
                    var response_data = jQuery.parseJSON(result.responseText)
                    if (response_data["code"] == 400) {
                        for (var k in response_data["error"]) {
                            form_obj.find("[name='" + k + "_error']").text(response_data["error"][k])
                        }
                    }else{
                        form_obj.prev().html(
                            '<div class="alert alert-danger">' +
                            '<i class="fa fa-times"></i> ' + response_data["msg"] +
                            '</div>'
                        )
                    }
                }else{
                    form_obj.prev().html(
                        '<div class="alert alert-danger">' +
                        '<i class="fa fa-times"></i> HTTP: 0 ' + result.statusText +
                        '</div>'
                    )
                }
            }
        })
}


function write_interval_chart(chartdata){
    /* 时间段画图 */
    chartobj = Highcharts.chart('log_chart', {
        chart: {
            type: 'spline',
            zoomType: 'x'
        },
        title: chartdata["title"],

        subtitle: chartdata["subtitle"],

        xAxis: {
            type: 'datetime',
            title: {
                text: '时间'
            },
            min: chartdata['xAxis']["min"],
            max: chartdata['xAxis']["max"]
        },
        yAxis: {
            title: {
                text: '行数'
            },
            min: 0
        },
        tooltip: {
            valueSuffix: '',
            shared: true,
            crosshairs: true,

            dateTimeLabelFormats: {
                minute:"%Y-%m-%d %H:%M",
            },
        },
        plotOptions: {
            spline: {
                marker: {
                    enabled: true
                }
            },

        },
        series: chartdata["series"],
        credits: {
            text: 'Loggrove',
            href: ''
        },
        global: {
            useUTC: false,
        }
    });
}