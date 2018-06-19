/**
 * Created by zhouwang on 2018/5/12.
 */

function write_new_row(id){
    $.ajax({
        url:"/local_log/file/" + id + "/",
        type:"GET",
        success:function(result){
            var response_data = jQuery.parseJSON(result)
            var data = response_data["data"]
            for(var i=0; i<data.length; i++){
                local_log_file_datatable.row.add( [
                    data[i]["path"],
                    data[i]["comment"],
                    data[i]["create_time"],
                    "<button class='btn btn-xs btn-danger perm' " +
                                    "onclick='delete_file(" + data[i]["id"] + ")'>删除</button>&nbsp;" +
                                "<button class='btn btn-xs btn-warning perm' " +
                                    "onclick='open_update_file_modal(" + data[i]["id"] + ")'>编辑</button>&nbsp;" +
                                "<button class='btn btn-xs btn-primary' " +
                                    "onclick='open_monitor_item_modal(" + data[i]["id"] + ")'>监控项</button>",
                    ]).draw().nodes().to$().attr('id', 'tr'+data[i]["id"])
            }
        },
        error:function(result){}
    })
}

function add_file(){
    var form_obj = $("#add_local_log_file_form")
    form_obj.prev().empty()
    $(".error_text").empty()

    var form_data = form_obj.serialize()
    $.ajax({
        url:"/local_log/file/",
        type:"POST",
        data:form_data,
        success:function (result) {
            var response_data = jQuery.parseJSON(result)
            form_obj.prev().html(
                '<div class="alert alert-success">' +
                '<i class="fa fa-check"></i> ' + response_data["msg"] +
                '</div>'
            )
            var id = response_data["data"][0]["id"]
            write_new_row(id)
        },
        error:function (result) {
            if (result.status != 0) {
                var response_data = jQuery.parseJSON(result.responseText)
                if (response_data["code"] == 400) {
                    for (var k in response_data["error"]) {
                        form_obj.find("[name='" + k + "']").next().text(response_data["error"][k])
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

function delete_file(id){
    var r = confirm("确定删除？");
    if(r == false){
        return false
    }

    $.ajax({
        url:"/local_log/file/" + id +"/",
        type:"DELETE",
        data:{'_xsrf':get_cookie('_xsrf')},
        success:function(result){
            local_log_file_datatable.row('#tr'+id).remove().draw(false);
            alert("删除成功！")
        },
        error:function(result){
            alert("删除失败！")
        }
    })
}

function update_file(id){
    var form_obj = $("#update_local_log_file_form")
    form_obj.prev().empty()
    $(".error_text").empty()

    var form_data = {
        'path':form_obj.find("input[name='path']").val(),
        'comment':form_obj.find("input[name='comment']").val(),
        '_xsrf':get_cookie('_xsrf')
    }

    $.ajax({
        url:"/local_log/file/" + id + "/",
        type:"PUT",
        data:form_data,
        success:function(result){
            var response_data = jQuery.parseJSON(result)
            form_obj.prev().html(
                '<div class="alert alert-success">' +
                '<i class="fa fa-check"></i> ' + response_data["msg"] +
                '</div>'
            )
            var tr = $("#tr"+id)
            local_log_file_datatable.cell(tr.children("td:eq(0)")).data(form_data["path"])
            local_log_file_datatable.cell(tr.children("td:eq(1)")).data(form_data["comment"])
        },
        error:function(result) {
            if (result.status != 0) {
                var response_data = jQuery.parseJSON(result.responseText)
                if (response_data["code"] == 400) {
                    for (var k in response_data["error"]) {
                        form_obj.find("[name='" + k + "']").next().text(response_data["error"][k])
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


function open_update_file_modal(id){
    var form_obj = $("#update_local_log_file_form")
    form_obj.prev().empty()
    $(".error_text").empty()

    var tr = $("#tr"+id)
    form_obj.find("input[name='path']").val(tr.children("td:eq(0)").text())
    form_obj.find("input[name='comment']").val(tr.children("td:eq(1)").text())
    $("#updateModal .modal-footer").children("button:eq(1)").attr("onclick", "update_file(" +id+ ")")
    $("#updateModal").modal("show")
}


function open_monitor_item_modal(local_log_file_id){
    $("#monitorItemModal .modal-body").empty()
    $.ajax({
        url:"/local_log/monitor/item/",
        type:"GET",
        data:{"local_log_file_id":local_log_file_id},
        success:function(result){
            var response_data = jQuery.parseJSON(result)
            for(var i=0;i<response_data["data"].length;i++){
                new_monitor_item_form(local_log_file_id)
                var new_form = $("#monitorItemModal .modal-body .row .col-sm-12").find("form").last()
                new_form.find("[name='id']").val(response_data["data"][i]["id"])
                new_form.find("[name='search_pattern']").val(response_data["data"][i]["search_pattern"])
                new_form.find("[name='local_log_file_id']").val(response_data["data"][i]["local_log_file_id"])
                new_form.find("[name='crontab_cycle']").val(response_data["data"][i]["crontab_cycle"])
                new_form.find("[name='check_interval']").val(response_data["data"][i]["check_interval"])
                new_form.find("[name='trigger_format']").val(response_data["data"][i]["trigger_format"])
                new_form.find("[name='dingding_webhook']").val(response_data["data"][i]["dingding_webhook"])
                new_form.find("[name='comment']").val(response_data["data"][i]["comment"])
                new_form.find("[name='alert']").val(response_data["data"][i]["alert"])
            }
            new_monitor_item_form(local_log_file_id)
        },
        error:function(result){}
    })
    $("#monitorItemModal").modal("show")
}


function save_monitor_item(_this){
    var form_obj = $(_this).parent()
    if(form_obj.find("input[name='id']").val()){
        update_monitor_item(form_obj)
    }else{
        add_monitor_item(form_obj)
    }
}


function del_monitor_item(_this){
    var id = $(_this).parent().find("[name='id']").val()
    if(!id){
        return false
    }
    var r = confirm("确定删除？");
    if(r == false){
        return false
    }

    $.ajax({
        url:"/local_log/monitor/item/" + id +"/",
        type:"DELETE",
        data:{'_xsrf':get_cookie('_xsrf')},
        success:function(result){
            $(_this).parent().parent().parent().remove()
            alert("删除成功！")
        },
        error:function(result){
            alert("删除失败！")
        }
    })
}

function update_monitor_item(form_obj){
    form_obj.prev().empty()
    form_obj.find(".error_text").empty()
    var form_data = form_obj.serialize()
    var id = form_obj.find("input[name='id']").val()
    $.ajax({
        url:"/local_log/monitor/item/" + id + "/",
        type:"PUT",
        data:form_data,
        success:function(result){
            var response_data = jQuery.parseJSON(result)
            form_obj.prev().html(
                '<div class="alert alert-success">' +
                '<i class="fa fa-check"></i> ' + response_data["msg"] +
                '</div>'
            )
        },
        error:function(result){
            if (result.status != 0) {
                var response_data = jQuery.parseJSON(result.responseText)
                if (response_data["code"] == 400) {
                    for (var k in response_data["error"]) {
                        form_obj.find("*[name='" + k + "']").next().text(response_data["error"][k])
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


function add_monitor_item(form_obj){
    form_obj.prev().empty()
    form_obj.find(".error_text").empty()
    var form_data = form_obj.serialize()
    $.ajax({
        url:"/local_log/monitor/item/",
        type:"POST",
        data:form_data,
        success:function(result){
            var response_data = jQuery.parseJSON(result)
            form_obj.prev().html(
                '<div class="alert alert-success">' +
                '<i class="fa fa-check"></i> ' + response_data["msg"] +
                '</div>'
            )
            var id = response_data["data"][0]["id"]
            form_obj.find("input[name='id']").val(id)
            new_monitor_item_form(form_obj.find("input[name='local_log_file_id']").val())
        },
        error:function(result){
            if (result.status != 0) {
                var response_data = jQuery.parseJSON(result.responseText)
                if (response_data["code"] == 400) {
                    for (var k in response_data["error"]) {
                        form_obj.find("*[name='" + k + "']").next().text(response_data["error"][k])
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


function new_monitor_item_form(local_log_file_id){
    $("#monitorItemModal .modal-body").append(
        '<div class="row">' +
            '<div class="col-sm-12">' +
                '<div class="panel panel-default">' +
                    '<div class="panel-heading"></div>' +
                    '<div class="panel-body">' +
                        '<div></div>' +
                        '<form role="form" class="form-horizontal">' +
                            '<input type="hidden" name="id">' +
                            '<input type="hidden" name="local_log_file_id" value="'+local_log_file_id+'">' +
                            '<input type="hidden" name="_xsrf" value="'+get_cookie('_xsrf')+'">' +
                            '<div class="form-group">' +
                                '<div class="col-sm-6">' +
                                    '<label>匹配模式 *</label>' +
                                    '<input class="form-control input-sm" name="search_pattern" placeholder="Regular pattern">' +
                                    '<span class="error_text"></span>' +
                                '</div>' +
                                '<div class="col-sm-6">' +
                                    '<label>备注 *</label>' +
                                    '<input class="form-control input-sm" name="comment" placeholder="Comment">' +
                                    '<span class="error_text"></span>' +
                                '</div>' +
                            '</div>' +
                            '<div class="form-group">' +
                                '<div class="col-sm-2">' +
                                    '<label>告警</label>' +
                                    '<select class="form-control input-sm" name="alert" disabled="disabled">' +
                                        '<option value="2">关闭</option>' +
                                        '<option value="1">开启</option>' +
                                    '</select>' +
                                    '<span class="error_text"></span>' +
                                '</div>' +
                                '<div class="col-sm-4">' +
                                    '<label>检查周期</label>' +
                                    '<input class="form-control input-sm" name="crontab_cycle" disabled="disabled" placeholder="Crontab cycle: */10 * * * *">' +
                                    '<span class="error_text"></span>' +
                                '</div>' +
                                '<div class="col-sm-2">' +
                                    '<label>检查区间（分钟）</label>' +
                                    '<input class="form-control input-sm" type="number" name="check_interval" disabled="disabled" placeholder="Interval: 10">' +
                                    '<span class="error_text"></span>' +
                                '</div>' +
                                '<div class="col-sm-4">' +
                                    '<label>触发公式</label>' +
                                    '<input class="form-control input-sm" type="text"  name="trigger_format" disabled="disabled" placeholder="Format: 0<{}<10">' +
                                    '<span class="error_text"></span>' +
                                '</div>' +
                            '</div>' +
                            '<div class="form-group">' +
                                '<div class="col-sm-12">' +
                                    '<label>钉钉webhook</label>' +
                                    '<input class="form-control input-sm" type="text" name="dingding_webhook" disabled="disabled" placeholder="Dingding webhook url">' +
                                    '<span class="error_text"></span>' +
                                '</div>' +
                            '</div>' +
                            '<button type="button" class="btn btn-primary btn-sm perm" style="float: right; margin-left: 15px" onclick="save_monitor_item(this)">保存</button>' +
                            '<button type="button" class="btn btn-danger btn-sm perm" style="float: right" onclick="del_monitor_item(this)">删除</button> ' +
                        '</form>' +
                    '</div>' +
                '</div>' +
            '</div>' +
        '</div>'
    )
}