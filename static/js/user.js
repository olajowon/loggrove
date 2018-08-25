/**
 * Created by zhouwang on 2018/6/2.
 */

function add_new_row(id){
    $.ajax({
        url:"/users/" + id + "/",
        type:"GET",
        success:function(result){
            var response_data = jQuery.parseJSON(result)
            var data = response_data["data"]
            var rows = []
            for(var i=0; i<data.length; i++){
                data[i]["option"] = "<button class='btn btn-xs btn-danger role1' " +
                                    "onclick='delete_user(" + data[i]["id"] + ")'>删除</button>&nbsp;" +
                                "<button class='btn btn-xs btn-warning role1' " +
                                    "onclick='open_update_modal(" + data[i]["id"] + ")'>编辑</button>&nbsp;" +
                                "<button class='btn btn-xs btn-primary role1' " +
                                    "onclick='open_reset_password_modal(" + data[i]["id"] + ")'>重置密码</button>"
                rows.push(data[i])
            }
            $("#user_table").bootstrapTable('prepend', rows);
        },
        error:function(result){}
    })
}

function add_user(){
    var form_obj = $("#add_user_form")
    form_obj.prev().empty()
    $(".error_text").empty()

    var form_data = form_obj.serialize()
    $.ajax({
        url:"/users/",
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


function update_user(id){
    var form_obj = $("#update_user_form")
    form_obj.prev().empty()
    $(".error_text").empty()

    var form_data = {
        'username':form_obj.find("input[name='username']").val(),
        'fullname':form_obj.find("input[name='fullname']").val(),
        'email':form_obj.find("input[name='email']").val(),
        'status':form_obj.find("select[name='status']").val(),
        'role':form_obj.find("select[name='role']").val(),
        '_xsrf':get_cookie('_xsrf')
    }

    $.ajax({
        url:"/users/" + id + "/",
        type:"PUT",
        data:form_data,
        success:function(result){
            var response_data = jQuery.parseJSON(result)
            form_obj.prev().html(
                '<div class="alert alert-success">' +
                '<i class="fa fa-check"></i> ' + response_data["msg"] +
                '</div>'
            )

            $("#user_table").bootstrapTable('updateByUniqueId', {
                id: id,
                row: {
                    username: form_data["username"],
                    fullname: form_data["fullname"],
                    email: form_data["email"],
                    status: form_data["status"],
                    role: form_data["role"],
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


function delete_user(id){
    var r = confirm("确定删除？");
    if(r == false){
        return false
    }

    $.ajax({
        url:"/users/" + id +"/",
        type:"DELETE",
        data:{'_xsrf':get_cookie('_xsrf')},
        success:function(result){
            $("#user_table").bootstrapTable('remove', {
                field: 'id',
                values: [id,]
            });
            alert("删除成功！")
        },
        error:function(result){
            alert("删除失败！")
        }
    })
}


function open_update_modal(id){
    var form_obj = $("#update_user_form")
    form_obj.prev().empty()
    $(".error_text").empty()

    var row = $("#user_table").bootstrapTable('getRowByUniqueId', id)

    form_obj.find("input[name='username']").val(row["username"])
    form_obj.find("input[name='fullname']").val(row["fullname"])
    form_obj.find("input[name='email']").val(row["email"])
    form_obj.find("select[name='status'] option").filter(function(){return $(this).val()==row["status"]}).prop("selected", true);
    form_obj.find("select[name='role'] option").filter(function(){return $(this).val()==row["role"]}).prop("selected", true);
    $("#updateModal .modal-footer").children("button:eq(1)").attr("onclick", "update_user(" +id+ ")")
    $("#updateModal").modal("show")
}


function open_reset_password_modal(id){
    var form_obj = $("#reset_password_form")
    form_obj.prev().empty()
    form_obj[0].reset()
    $(".error_text").empty()
    $("#resetPasswordModal .modal-footer").children("button:eq(1)").attr("onclick", "reset_password(" +id+ ")")
    $("#resetPasswordModal").modal("show")
}


function reset_password(id){
    var form_obj = $("#reset_password_form")
    form_obj.prev().empty()
    $(".error_text").empty()

    var password = form_obj.find("input[name='password']").val()
    var confirm_password = form_obj.find("input[name='confirm_password']").val()

    if(!password){
        form_obj.find("input[name='password']").next().text("请输入密码")
        return false
    }
    if(!confirm_password){
        form_obj.find("input[name='confirm_password']").next().text("请输入确认密码")
        return false
    }
    if(password != confirm_password){
        form_obj.find("input[name='confirm_password']").next().text("错误的确认密码")
        return false
    }
    if(password.length < 6){
        form_obj.find("input[name='confirm_password']").next().text("密码不可少于6个字符")
        return false
    }

    var form_data = form_obj.serialize()
    $.ajax({
        url:"/users/"+ id +"/password/",
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

$(function(){
    $('#addModal').on('show.bs.modal', function (){
        $("#add_user_form").prev().empty()
        $("#add_user_form")[0].reset()
        $(".error_text").empty()
    })
})