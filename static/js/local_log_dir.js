/**
 * Created by zhouwang on 2018/5/21.
 */

function write_new_panels(data){
    for(var i=0; i<data.length; i++){
        $("#panelgroup").prepend(
            '<div class="panel panel-default" id="panel'+ data[i]["id"] +'" style="margin-bottom: 15px">' +
                '<div class="panel-heading">' +
                    '<i class="fa fa-folder fa-fw" style="cursor:pointer" data-toggle="collapse" data-parent="#panelgroup" href="#panelcollapse'+ data[i]["id"] +'"></i> <a style="color: black" data-toggle="collapse" data-parent="#panelgroup" href="#panelcollapse'+ data[i]["id"] +'">' + data[i]["path"] + '</a>'+
                    '<div class="pull-right">' +
                        '<button class="btn btn-xs btn-warning role2"'  +
                        'onclick="delete_dir(' + data[i]["id"] + ')">删除</button> ' +
                        '<button class="btn btn-xs btn-primary role2"'  +
                        'onclick="open_update_dir_modal(' + data[i]["id"] + ')">编辑</button>' +

                    '</div>' +
                '</div>' +
                '<div id="panelcollapse'+ data[i]["id"] +'" class="panel-collapse collapse">' +
                    '<div class="panel-body">' +
                        '<div style="border-bottom: 1px solid #ddd; margin-bottom: 15px">'+ data[i]["comment"] +'</div>' +
                        '<div class="row" style="margin-bottom: 15px">' +
                            '<div class="col-sm-4 col-xs-7">' +
                                '<input type="text" class="form-control input-sm" onkeyup="search_treeview_node(' + data[i]["id"] + ', $(this).val())" placeholder="Search..."> ' +

                            '</div>' +
                            '<div class="col-sm-8 col-xs-5">' +
                                '<div class="pull-right">' +
                                    '<button class="btn btn-sm btn-default" onclick="expand_treeview(' + data[i]["id"] + ')"><i class="fa fa-folder-open"></i></button> ' +
                                    '<button class="btn btn-sm btn-default" onclick="collapse_treeview(' + data[i]["id"] + ')"><i class="fa fa-folder"></i></button> ' +
                                '</div>' +
                            '</div>' +
                        '</div>' +

                        '<div id="treeview' + data[i]["id"]+ '"></div>' +
                    '</div>' +
                '</div>' +
            '</div>'
        )

        $('.panel-collapse').on('shown.bs.collapse', function(){
            $(this).prev().find("i").removeClass('fa-folder').addClass('fa-folder-open')
        });

        $('.panel-collapse').on('hidden.bs.collapse', function(){
            $(this).prev().find("i").removeClass('fa-folder-open').addClass('fa-folder')
        });
    }
}


function write_new_treeview(data) {
    for(var i=0; i<data.length; i++){
        var treeview_obj = $('#treeview'+data[i]["id"]).treeview({
            data: data[i]['nodes'],
            levels: 1,
            expandIcon: "fa fa-folder fa-fw",
            collapseIcon: "fa fa-folder-open fa-fw",
            emptyIcon:"fa fa-file",
            enableLinks:false,
            showBorder:true,
            highlightSelected: false,
        });
        treeview_map['treeview'+data[i]["id"]] = treeview_obj
    }
}

function add_dir(){
    var form_obj = $("#add_local_log_dir_form")
    form_obj.prev().empty()
    $(".error_text").empty()

    var form_data = form_obj.serialize()
    $.ajax({
        url:"/local_log/dir/",
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
            $.get("/local_log/dir/"+id+"/",function(data,status){
                var response_data = jQuery.parseJSON(data)
                write_new_panels(response_data["data"])
                write_new_treeview(response_data["data"])
                $("#panelcollapse" + id).collapse("show")
            });
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


function delete_dir(id){
    var r = confirm("确定删除？");
    if(r == false){
        return false
    }

    $.ajax({
        url:"/local_log/dir/" + id +"/",
        type:"DELETE",
        data:{'_xsrf': get_cookie('_xsrf')},
        success:function(result){
            $("#panel"+id).remove()
            //treeview_map['treeview'+id].treeview('remove')
            alert("删除成功！")
        },
        error:function(result){
            alert("删除失败！")
        }
    })
}

function update_dir(id){
    var form_obj = $("#update_local_log_dir_form")
    form_obj.prev().empty()
    $(".error_text").empty()

    var form_data = form_obj.serialize()
    $.ajax({
        url:"/local_log/dir/" + id + "/",
        type:"PUT",
        data:form_data,
        success:function(result){
            var response_data = jQuery.parseJSON(result)
            form_obj.prev().html(
                '<div class="alert alert-success">' +
                '<i class="fa fa-check"></i> ' + response_data["msg"] +
                '</div>'
            )


            $.get("/local_log/dir/"+id+"/",function(data,status){
                var response_data = jQuery.parseJSON(data)
                var panel = $("#panel"+id)
                panel.find(".panel-heading a").text(response_data["data"][0]["path"])
                panel.find(".panel-collapse .panel-body div").eq(0).text(response_data["data"][0]["comment"])
                write_new_treeview(response_data["data"])
            });

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

function open_update_dir_modal(id){
    var form_obj = $("#update_local_log_dir_form")
    form_obj.prev().empty()
    $(".error_text").empty()

    var panel = $("#panel"+id)
    form_obj.find("input[name='path']").val(panel.find(".panel-heading a").text())
    form_obj.find("input[name='comment']").val(panel.find(".panel-collapse .panel-body div").eq(0).text())
    $("#updateModal .modal-footer").children("button:eq(1)").attr("onclick", "update_dir(" +id+ ")")
    $("#updateModal").modal("show")
}