/**
 * Created by zhouwang on 2018/8/12.
 */
 
websocket = null

function logfile_keepread(_this){
    if(websocket){
        alert('需要先关闭上一次连接或刷新页面！')
        return false
    }

    $("form .error_text").empty()
    var form_obj = $(_this).parent()
    var logfile_id = form_obj.find("select[name='logfile_id']").val()
    var other_search_pattern = form_obj.find("input[name='other_search_pattern']").val()
    if(other_search_pattern){
        var search_pattern = other_search_pattern
    }else{
        var search_pattern = form_obj.find("select[name='search_pattern']").val()
    }
    var filter_search_line = form_obj.find("input[name='filter_search_line']:checked").val()
    if(!logfile_id){
        form_obj.find("span[name='logfile_id_error']").text('日志路径是必选项')
        return false
    }

    $("#log_content_row").show()

    var log_content_html = "连接中 [Connection] ...<br>"
    $("#log_content").html(log_content_html)

    if(filter_search_line){
        var host = "ws://" + location.hostname + ":" + location.port +
            "/keepread/?logfile_id="+ logfile_id +"&search_pattern="+ search_pattern
    }else{
        var host = "ws://" + location.hostname + ":" + location.port + "/local_log/keepread/?logfile_id="+ logfile_id
    }

    websocket = new WebSocket(host)

    websocket.onopen = function(evt){
        $("#log_content").empty()
        $("#log_stat_row").show()
        $("#total_size").text(0)
        $("#total_lines").text(0)
        $("#size").text(0)
        $("#lines").text(0)
        $("#highlight_lines").text(0)
        $("#window_lines").text(0)
        $("#log_content").append("<span style='color: green'>连接成功 [Connection successful] ...</span><br><br>")
    }
    websocket.onmessage = function(evt){    // 获取服务器返回的信息
        var result = $.parseJSON(evt.data)
        if(result['code']==0){
            var search_result = log_content_searching(result["data"]["contents"], search_pattern)
            $("#log_content").append(search_result["log_content"])
            $("#total_size").text((result['data']['total_size']/1024).toFixed(2))
            $("#total_lines").text((result['data']['total_lines']))
            $("#size").text((parseInt($("#size").text()) + (result['data']['size']/1024)).toFixed(2))
            $("#lines").text(parseInt($("#lines").text()) + result['data']['lines'])
            $("#highlight_lines").text(parseInt($("#highlight_lines").text()) + search_result['highlight_lines'])
            $("#window_lines").text(parseInt($("#window_lines").text()) + result["data"]["lines"])
            console.log(check_in)
            if(!check_in) {
                $("#log_content").scrollTop($("#log_content")[0].scrollHeight);
            }
        }else{

            if(result['code']==400){
                for (var k in result["error"]) {
                    form_obj.find("[name='"+ k +"_error']").text(result["error"][k])
                }
            }

            $("#log_content").append(
                '<span class="error_text">' + "错误 [Code: "+ result["code"] + "] " + result["msg"] + "</span><br>"
                + (
                result["detail"]
                    ?
                '<span class="error_text">' + result["detail"] + "</span><br>"
                    :
                ''
                )
            )

            if(!check_in) {
                $("#log_content").scrollTop($("#log_content")[0].scrollHeight);
            }
            websocket.close()
        }
    }

    websocket.onerror = function(evt){
        $("#log_content").append("<br><span class=\"error_text\">连接失败 [Connection failed] ...</span><br>")
        websocket = null
        if(!check_in){
            $("#log_content").scrollTop($("#log_content")[0].scrollHeight);
        }
    }

    websocket.onclose = function(evt){
        $("#log_content").append("<br><span class=\"error_text\">连接关闭 [Connection closed] ...</span><br>")
        console.log('onclose')
        if(!check_in) {
            $("#log_content").scrollTop($("#log_content")[0].scrollHeight);
        }
        websocket = null
    }
}


function close_websocket(){
    console.log('close')
    if(websocket){
        websocket.close()
    }
}

function clear_log_content(){
    $("#log_content").empty()
    $("#window_lines").text(0)
}