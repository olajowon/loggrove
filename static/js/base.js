/**
 * Created by zhouwang on 2018/5/16.
 */

function get_cookie(key) {
    var cookie = document.cookie.match("\\b" + key + "=([^;]*)\\b");
    return cookie ? cookie[1] : undefined;
}

function get_language(){
    var language = document.cookie.match("\\b" + 'language' + "=([^;]*)\\b");
    console.log(language)
    return language? language[1] : "cn"
}

function log_content_searching(lines, search_pattern){
    var content_html = ""
    var highlight_lines = 0
    for(var i=0;i<lines.length;i++){
        var line = lines[i]
        if(line){
            line = line.replace(/</g, "&lt;").replace(/>/g, "&gt;")
            if(search_pattern){
                var reg = new RegExp(search_pattern,'g')
                var match_arr = line.match(reg)
                if(match_arr){
                    content_html += (line.replace(new RegExp(match_arr[0]), '<b style="background-color: yellow">' + match_arr[0]+ "</b>") + "<br>")
                    highlight_lines += 1
                    continue
                }
            }
            content_html += (line + "<br>")
        }
    }
    return {'log_content': content_html, 'highlight_lines':highlight_lines}
}


function logout(){
    $.ajax({
        url:"/logout/",
        type:"POST",
        data:{"_xsrf":get_cookie("_xsrf")},
        success:function(result){
            window.location.href = "/login/html/"
        },
        error:function(result){}
    })
}


function change_password(){
    var form_obj = $("#change_password_form")
    $(".error_text").empty()
    form_obj.prev().empty()
    var old_password = form_obj.find("input[name='old_password']").val()
    var new_password = form_obj.find("input[name='new_password']").val()
    var confirm_password = form_obj.find("input[name='confirm_password']").val()
    if(!old_password){
        form_obj.find("input[name='old_password']").next().text("Required")
        return false
    }
    if(!new_password){
        form_obj.find("input[name='new_password']").next().text("Required")
        return false
    }
    if(!confirm_password){
        form_obj.find("input[name='confirm_password']").next().text("Required")
        return false
    }
    if(new_password != confirm_password){
        form_obj.find("input[name='confirm_password']").next().text("Confirm password is incorrect")
        return false
    }
    if(new_password.length < 6){
        form_obj.find("input[name='new_password']").next().text("Must be more than 6 characters")
        return false
    }
    var data = {
        "old_password":old_password,
        "new_password":new_password,
        "_xsrf":get_cookie("_xsrf")
    }

    $.ajax({
        url:"/password/",
        type:"PUT",
        data:data,
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


function open_show_profile_modal(){
    $.ajax({
        url:"/profile/",
        type:"GET",
        data:'',
        success:function (result) {
            var response_data = jQuery.parseJSON(result)
            var cite_objs = $("#profileModal").find("cite")
            cite_objs.eq(0).text(response_data["data"][0]["username"])
            cite_objs.eq(1).text(response_data["data"][0]["id"])
            cite_objs.eq(2).text(response_data["data"][0]["fullname"])
            cite_objs.eq(3).text(response_data["data"][0]["email"])
            cite_objs.eq(4).text((response_data["data"][0]["role"]=="1" ? _("Superadmin") : (response_data["data"][0]=="2" ? _("Admin") : _("Ordinaryuser"))))
            cite_objs.eq(5).text(response_data["data"][0]["join_time"])
            cite_objs.eq(6).text(response_data["data"][0]["login_time"])
            cite_objs.eq(7).text(response_data["data"][0]["expire_time"])

        },
        error:function (result) {}
    })
    $("#profileModal").modal("show")
}

$(function(){
    $('#changePasswordModal').on('show.bs.modal', function (){
        $("#change_password_form").prev().empty()
        $("#change_password_form")[0].reset()
        $(".error_text").empty()
    })
})
