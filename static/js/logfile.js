/**
 * Created by zhouwang on 2018/8/8.
 */

function add_logfile(){
    var form_obj = $("#add_logfile_form")
    form_obj.prev().empty()
    $(".error_text").empty()

    var form_data = form_obj.serialize()
    $.ajax({
        url:"/logfiles/",
        type:"POST",
        data:form_data,
        success:function (result) {
            var response_data = jQuery.parseJSON(result)
            form_obj.prev().html(
                '<div class="alert alert-success">' +
                '<i class="fa fa-check"></i> ' + response_data["msg"] +
                '</div>'
            )
            var id = response_data["data"]["id"]
            add_new_row(id)
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


function add_new_row(id){
    $.ajax({
        url:"/logfiles/" + id + "/",
        type:"GET",
        success:function(result){
            var response_data = jQuery.parseJSON(result)
            var data = response_data["data"]
            var rows = []
            for(var i=0; i<data.length; i++){
                data[i]["option"] = "<button class='btn btn-xs btn-danger role2' " +
                                    "onclick='delete_logfile(" + data[i]["id"] + ")'>删除</button>&nbsp;" +
                                "<button class='btn btn-xs btn-warning role2' " +
                                    "onclick='open_update_file_modal(" + data[i]["id"] + ")'>编辑</button>&nbsp;" +
                                "<button class='btn btn-xs btn-info' " +
                                    "onclick='open_chart_modal(" + data[i]["id"] + ")'>图表</button>&nbsp;" +
                                "<button class='btn btn-xs btn-primary' " +
                                    "onclick='open_monitor_item_modal(" + data[i]["id"] + ")'>监控项</button>"
                rows.push(data[i])
            }
            $("#logfile_table").bootstrapTable('prepend', rows);
        },
        error:function(result){}
    })
}

function delete_logfile(id){
    var r = confirm(_("Do you want to delete it") + "？");
    if(r == false){
        return false
    }

    $.ajax({
        url:"/logfiles/" + id +"/",
        type:"DELETE",
        data:{'_xsrf':get_cookie('_xsrf')},
        success:function(result){
            $("#logfile_table").bootstrapTable('remove', {
                field: 'id',
                values: [id,]
            });
            alert(_("Delete successful"))
        },
        error:function(result){
            alert(_("Delete failed"))
        }
    })
}


function open_update_modal(id){
    var form_obj = $("#update_logfile_form")
    form_obj.prev().empty()
    form_obj.find('[name="host"]').tagsinput('removeAll')
    $(".error_text").empty()

    var row = $("#logfile_table").bootstrapTable('getRowByUniqueId', id)
    var monitor_choice = row["monitor_choice"]
    form_obj.find("input[name='monitor_choice']").each(function(){
        if($(this).val() == monitor_choice){
            $(this).prop("checked", true)
        }
    })
    form_obj.find("input[name='name']").val(row["name"])
    form_obj.find("input[name='host']").tagsinput('add', row["host"])
    form_obj.find("input[name='path']").val(row["path"])
    form_obj.find("input[name='comment']").val(row["comment"])
    $("#updateModal .modal-footer").children("button:eq(1)").attr("onclick", "update_logfile(" +id+ ")")
    $("#updateModal").modal("show")
}


function update_logfile(id){
    var form_obj = $("#update_logfile_form")
    form_obj.prev().empty()
    $(".error_text").empty()

    var form_data = {
        'name':form_obj.find("input[name='name']").val(),
        'host':form_obj.find("input[name='host']").val(),
        'path':form_obj.find("input[name='path']").val(),
        'comment':form_obj.find("input[name='comment']").val(),
        'monitor_choice':form_obj.find("input[name='monitor_choice']:checked").val(),
        '_xsrf':get_cookie('_xsrf')
    }

    $.ajax({
        url:"/logfiles/" + id + "/",
        type:"PUT",
        data:form_data,
        success:function(result){
            var response_data = jQuery.parseJSON(result)
            form_obj.prev().html(
                '<div class="alert alert-success">' +
                '<i class="fa fa-check"></i> ' + response_data["msg"] +
                '</div>'
            )

            $("#logfile_table").bootstrapTable('updateByUniqueId', {
                id: id,
                row: {
                    name: form_data["name"],
                    host: form_data["host"],
                    path: form_data["path"],
                    comment: form_data["comment"],
                    monitor_choice: form_data["monitor_choice"],
                }
            })
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


function open_monitor_item_modal(logfile_id){
    $("#monitorItemModal .modal-body").empty()
    $.ajax({
        url:"/monitor/items/",
        type:"GET",
        data:{"logfile_id":logfile_id},
        success:function(result){
            var response_data = jQuery.parseJSON(result)
            for(var i=0;i<response_data["data"].length;i++){
                new_monitor_item_form(logfile_id)
                var new_form = $("#monitorItemModal .modal-body .row .col-sm-12").find("form").last()
                new_form.find("[name='id']").val(response_data["data"][i]["id"])
                new_form.find("[name='name']").val(response_data["data"][i]["name"])
                new_form.find("[name='match_regex']").val(response_data["data"][i]["match_regex"])
                new_form.find("[name='logfile_id']").val(response_data["data"][i]["logfile_id"])
                new_form.find("[name='crontab_cycle']").val(response_data["data"][i]["crontab_cycle"])
                new_form.find("[name='intervals']").val(response_data["data"][i]["intervals"])
                new_form.find("[name='expression']").val(response_data["data"][i]["expression"])
                new_form.find("[name='webhook']").val(response_data["data"][i]["webhook"])
                new_form.find("[name='comment']").val(response_data["data"][i]["comment"])
                new_form.find("[name='alert']").val(response_data["data"][i]["alert"])
            }
            new_monitor_item_form(logfile_id)
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
    var r = confirm(_("Do you want to delete it") + "？");
    if(r == false){
        return false
    }

    $.ajax({
        url:"/monitor/items/" + id +"/",
        type:"DELETE",
        data:{'_xsrf':get_cookie('_xsrf')},
        success:function(result){
            $(_this).parent().parent().parent().remove()
            alert(_("Delete successful"))
        },
        error:function(result){
            alert(_("Delete failed"))
        }
    })
}

function update_monitor_item(form_obj){
    form_obj.prev().empty()
    form_obj.find(".error_text").empty()
    var form_data = form_obj.serialize()
    var id = form_obj.find("input[name='id']").val()
    $.ajax({
        url:"/monitor/items/" + id + "/",
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
        url:"/monitor/items/",
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
            new_monitor_item_form(form_obj.find("input[name='logfile_id']").val())
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


function new_monitor_item_form(logfile_id){
    $("#monitorItemModal .modal-body").append(
        '<div class="row">' +
            '<div class="col-sm-12">' +
                '<div class="panel panel-default">' +
                    '<div class="panel-body">' +
                        '<div></div>' +
                        '<form role="form" class="form-horizontal">' +
                            '<input type="hidden" name="id">' +
                            '<input type="hidden" name="logfile_id" value="'+logfile_id+'">' +
                            '<input type="hidden" name="_xsrf" value="'+get_cookie('_xsrf')+'">' +
                            '<div class="form-group">' +
                                '<div class="col-sm-4">' +
                                    '<label>'+ _("Name") +' *</label>' +
                                    '<input class="form-control input-sm" name="name" placeholder="Name">' +
                                    '<span class="error_text"></span>' +
                                '</div>' +
                                '<div class="col-sm-4">' +
                                    '<label>'+ _("Match") +' *</label>' +
                                    '<input class="form-control input-sm" name="match_regex" placeholder="Regular pattern">' +
                                    '<span class="error_text"></span>' +
                                '</div>' +
                                '<div class="col-sm-4">' +
                                    '<label>'+ _("Comment") +'</label>' +
                                    '<input class="form-control input-sm" name="comment" placeholder="Comment">' +
                                    '<span class="error_text"></span>' +
                                '</div>' +
                            '</div>' +
                            '<div class="form-group">' +
                                '<div class="col-sm-3">' +
                                    '<label>'+ _("Alert") +'</label>' +
                                    '<select class="form-control input-sm" name="alert">' +
                                        '<option value="2">'+ _("Close") +'</option>' +
                                        '<option value="1">'+ _("Open") +'</option>' +
                                    '</select>' +
                                    '<span class="error_text"></span>' +
                                '</div>' +
                                '<div class="col-sm-3">' +
                                    '<label>'+ _("Intervals") +' (m)</label>' +
                                    '<input class="form-control input-sm" type="number" name="intervals" placeholder="Intervals: number">' +
                                    '<span class="error_text"></span>' +
                                '</div>' +
                                '<div class="col-sm-6">' +
                                    '<label>'+ _("Expression") +'</label>' +
                                    '<input class="form-control input-sm" type="text"  name="expression" placeholder="Format: n1<{}<n2">' +
                                    '<span class="error_text"></span>' +
                                '</div>' +
                            '</div>' +
                            '<div class="form-group">' +
                                '<div class="col-sm-12">' +
                                    '<label>'+ _("Webhook") +'</label>' +
                                    '<input class="form-control input-sm" type="text" name="webhook" placeholder="Webhook">' +
                                    '<span class="error_text"></span>' +
                                '</div>' +
                            '</div>' +
                            '<button type="button" class="btn btn-info btn-circle" onclick="open_monitor_item_explain_modal()" title="Monitor item description"><i class="fa fa-question"></i></button>' +
                            '<button type="button" class="btn btn-primary btn-sm role2" style="float: right; margin-left: 15px" onclick="save_monitor_item(this)">'+ _("Save") +'</button>' +
                            '<button type="button" class="btn btn-danger btn-sm role2" style="float: right" onclick="del_monitor_item(this)">'+ _("Delete") +'</button> ' +
                        '</form>' +
                    '</div>' +
                '</div>' +
            '</div>' +
        '</div>'
    )
}

function open_monitor_item_explain_modal() {
    var body_has_modal_open = $("body").is(".modal-open")
    if (body_has_modal_open){
        $("#monitorItemExplainModal").on('hidden.bs.modal', function () {
          $("body").addClass("modal-open")
        })
    }
    $("#monitorItemExplainModal").modal("show")
}

$(function(){
    $('#addModal').on('show.bs.modal', function (){
        $("#add_logfile_form").prev().empty()
        $("#add_logfile_form")[0].reset()
        $("#add_logfile_form").find('[name="host"]').tagsinput('removeAll')
        $(".error_text").empty()
    })
})





