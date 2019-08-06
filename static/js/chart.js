/**
 * Created by zhouwang on 2018/6/24.
 */

chartobj = null
interval = null
Highcharts.setOptions({global: {useUTC: false}})

function open_chart_modal(logfile_id){
    /* 图表modal */

    if(interval){
        window.clearInterval(interval)
    }

    $("#update_chart").empty()
    $("#chartModal").modal("show")

    var row = $("#logfile_table").bootstrapTable('getRowByUniqueId', logfile_id)
    var logfile = row["name"]
    var hosts = row["host"].split(",")
    var now = new Date();
    var end = strDateForChart(now);
    var begin = strDateForChart(new Date(now.setHours(now.getHours()-24)));
    var items = []
    $.ajax({
        url:"/monitor/items/",
        type:"GET",
        async: false,
        data:{"logfile_id": logfile_id},
        success:function(result){
            var response_data = jQuery.parseJSON(result)
            for(var i=0;i<response_data["data"].length;i++){
                items.push(response_data["data"][i]["name"])
            }
        },
        error:function(result){}
    })

    var monitor_items = [];
    for(var i=0; i<hosts.length; i++){
        for(var j=0; j<items.length; j++){
            monitor_items.push({logfile: logfile, host: hosts[i], monitor_item: items[j]})
        }
    }

    var get_data = {
        'begin_time': begin,
        'end_time': end,
        'items': JSON.stringify(monitor_items),
        'mode': 'interval'
    }

    $.ajax({
        url:"/charts/",
        type:"GET",
        data:get_data,
        success:function(result){
            var response_data = jQuery.parseJSON(result)
            var data = response_data["data"]

            var chartdata = {
                "title": {"text": _("24h logfile tendency chart")},
                "subtitle": {"text": logfile},
                "series": data["series"],
                "xAxis": data["xAxis"],
            }

            write_interval_chart(chartdata)

            interval = window.setInterval("update_24h_chart("+ JSON.stringify(get_data) +")", 30000);

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
    var now = new Date();
    var end = strDateForChart(now);
    var begin = strDateForChart(new Date(now.setHours(now.getHours()-24)));
    get_data.end_time = end;
    get_data.begin_time = begin;

    $.ajax({
        url:"/charts/",
        type:"GET",
        data:get_data,
        success:function(result){
            var response_data = jQuery.parseJSON(result)
            var data = response_data["data"]
            chartobj.xAxis[0].update({"min":data["xAxis"]["min"], "max":data["xAxis"]["max"]})
            chartobj.update({
                "series":data["series"]
            })
        },
        error:function(result){}
    })
}


function show_interval_chart(interval_option){
    /* 连续查询图表 */

    var begin = null;
    var end = null;
    if (interval_option){
        var now = new Date();
        end = strDateForChart(now);
        if (interval_option == "Last 1h"){
            begin = strDateForChart(new Date(now.setHours(now.getHours()-1)));
        }else if (interval_option == "Last 6h"){
            begin = strDateForChart(new Date(now.setHours(now.getHours()-6)));
        }else if (interval_option == "Last 12h"){
            begin = strDateForChart(new Date(now.setHours(now.getHours()-12)));
        }else if (interval_option == "Last 24h"){
            begin = strDateForChart(new Date(now.setHours(now.getHours()-24)));
        }else if (interval_option == "Last 2d"){
            begin = strDateForChart(new Date(now.setDate(now.getDate()-2)));
        }else if (interval_option == "Last 7d"){
            begin = strDateForChart(new Date(now.setDate(now.getDate()-7)));
        }
    }else{
        begin = $("input[name='begin_time']").val()
        end = $("input[name='end_time']").val()
    }

    if(interval){
        window.clearInterval(interval)
    }

    var form_obj = $("form")
    form_obj.prev().empty()
    $(".error_text").empty()
    $("#log_chart").parent().show()

    var monitor_items = [];
    $(".item-group").each(function () {
        var logfile = $(this).find("[name='logfile']").val()
        var hosts = $(this).find("[name='host']").val()
        var items = $(this).find("[name='monitor_item']").val()
        for(var i=0; i<hosts.length; i++){
            for(var j=0; j<items.length; j++){
                monitor_items.push({logfile: logfile, host: hosts[i], monitor_item: items[j]})
            }
        }
    })

    var get_data = {
        'begin_time': begin,
        'end_time': end,
        'items': JSON.stringify(monitor_items),
        'mode': 'interval'
    }

    $.ajax({
        url:"/charts/",
        type:"GET",
        data: get_data,
        success:function(result){
            var response_data = jQuery.parseJSON(result)
            var data = response_data["data"]
            var chartdata = {
                "title": {"text": _("Logfile tendency chart")},
                "subtitle": {"text": begin + " - " + end},
                "series": data["series"],
                "xAxis": data["xAxis"]
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


function show_contrast_chart(contrast_day){
    /* 日期对比查询 */

    var date
    if (contrast_day){
        date = today + "," + contrast_day
    } else {
        date = $("input[name='cdate']").val()
    }

    if(interval){
        window.clearInterval(interval)
    }

    var form_obj = $("form")
    form_obj.prev().empty()
    $(".error_text").empty()
    $("#log_chart").parent().show()
    var monitor_items = [];
    $(".item-group").each(function () {
        var logfile = $(this).find("[name='logfile']").val()
        var hosts = $(this).find("[name='host']").val()
        var items = $(this).find("[name='monitor_item']").val()
        for(var i=0; i<hosts.length; i++){
            for(var j=0; j<items.length; j++){
                monitor_items.push({logfile: logfile, host: hosts[i], monitor_item: items[j]})
            }
        }
    })

    var get_data = {
        'date': date,
        'items': JSON.stringify(monitor_items),
        'mode': 'contrast'
    }

    $.ajax({
        url:"/charts/",
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
                title: {"text": _("Logfile contrast chart")},
                subtitle: {"text": date},
                xAxis: {
                    type: 'datetime',
                    title: {
                        text: _("Datetime line")
                    },
                    min: data["xAxis"]["min"],
                    max: data["xAxis"]["max"],
                    labels: {
                        formatter:function () {
                            return Highcharts.dateFormat("%H:%M",this.value);
                        },
                    }
                },
                yAxis: {
                    title: {
                        text: _('Lines')
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
                series: data["series"],
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
        title: chartdata['title'],

        subtitle: chartdata['subtitle'],

        xAxis: {
            type: 'datetime',
            title: {
                text: _('Datetime line')
            },
            min: chartdata['xAxis']["min"],
            max: chartdata['xAxis']["max"]
        },
        yAxis: {
            title: {
                text: _('Lines')
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
        series: chartdata['series'],
        credits: {
            text: 'Loggrove',
            href: ''
        },
        global: {
            useUTC: false,
        }
    });
}

function add_item_group(_this){
    var html = '<div class="form-group item-group">' +
        '<div class="col-sm-3">' +
            '<input type="text" name="logfile" class="form-control" placeholder="'+ _("Logfile") +'" autocomplete="off" data-provide="typeahead">' +
             '<span name="logfile_error" class="error_text"></span>' +
        '</div>' +
        '<div class="col-sm-3">' +
            '<select class="form-control selectpicker" multiple name="host" data-live-search="true" title="'+_("Host")+'">' +
            '</select>' +
        '</div>' +
        '<div class="col-sm-3">' +
            '<select class="form-control selectpicker" multiple name="monitor_item" data-live-search="true" title="'+_("Monitor item")+'">' +
            '</select>' +
        '</div>' +
        '<div class="col-sm-3">' +
            '<div>' +
                '<button type="button" class="btn  btn-default" onclick="del_item_group(this)"><i class="fa fa-minus"></i></button> ' +
                '<button type="button" class="btn  btn-default" onclick="add_item_group(this)"><i class="fa fa-plus"></i></button>' +
            '</div>' +
        '</div>' +
    '</div>'
    $(_this).parent().parent().parent().after(html)
    var form_group_obj = $(_this).parent().parent().parent().next()
    form_group_obj.find("select[name='host']").selectpicker('refresh');
    form_group_obj.find("select[name='monitor_item']").selectpicker('render');

    form_group_obj.find("input[name='logfile']").typeahead({
        delay: 500,
        autoSelect: false,
        showHintOnFocus: true,
        selectOnBlur: false,
        changeInputOnSelect: true,
        source: function (search, process) {
            var param = {search: search, order: "asc", sort: "path", offset: 0, limit: 100};
            $.get('/logfiles/', param, function (response_data) {
                var data = jQuery.parseJSON(response_data).data
                process(data);
            });
        },
        matcher: function (items) {
            return items;
        },
        updater: function (item) {
            return item.name;
        },
        displayText: function (item) {
            return item.name;
        }
    });
}

function del_item_group(_this){
    if($(".item-group").length > 1){
        $(_this).parent().parent().parent().remove()
    }else{
        add_item_group(_this)
        $(_this).parent().parent().parent().remove()
    }
}