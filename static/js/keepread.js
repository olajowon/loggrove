/**
 * Created by zhouwang on 2018/8/12.
 */
 
websocket = null

function logfile_keepread(){
    if(websocket){
        alert(_("Please close the previous connection or refresh the page"))
        return false
    }

    $("form .error_text").empty()
    var form_obj = $("#logfile_form")
    var logfile = form_obj.find("input[name='logfile']").val()
    var host = form_obj.find("select[name='host']").val()
    var path = form_obj.find("select[name='path']").val()
    var match = form_obj.find("input[name='match']").val()
    var filter_search_line = form_obj.find("input[name='filter_search_line']:checked").val()
    if(!logfile){
        form_obj.find("span[name='logfile_error']").text("Required")
        return false
    }

    $("#log_content_row").show()

    var log_content_html = "Connection ...<br>"
    $("#log_content").html(log_content_html)

    if(filter_search_line){
        var wshost = "ws://" + location.hostname + ":" + location.port +
            "/keepread/?logfile="+ logfile +"&match="+ match +"&host="+ host +"&path="+ path;
    }else{
        var wshost = "ws://" + location.hostname + ":" + location.port +
            "/keepread/?logfile="+ logfile +"&host="+ host +"&path="+ path;
    }

    keep_lines = null;
    highlight_lines = null;
    window_lines = null;
    websocket = new WebSocket(wshost);
    websocket.onopen = function(evt){
        $("#log_content").empty()
        $("#keep_lines").text("--")
        $("#last_update").text("--")
        $("#highlight_lines").text("--")
        $("#window_lines").text("--")
        $("#log_content").append("<span style='color: green'>Connection successful ...</span><br><br>")
    }
    websocket.onmessage = function(evt){
        var result = $.parseJSON(evt.data)
        if(result['code']==0){
            var search_result = log_content_searching(result["data"]["contents"], match)

            keep_lines = result['data']['keep_lines']
            highlight_lines = highlight_lines + search_result['highlight_lines']
            window_lines = window_lines + result['data']['lines']
            $("#log_content").append(search_result["log_content"])
            $("#keep_lines").text(keep_lines)
            $("#highlight_lines").text(highlight_lines)
            $("#window_lines").text(window_lines)
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
                '<span class="error_text">' + "Error [Code: "+ result["code"] + "] " + result["msg"] + "</span><br>"
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
        $("#last_update").text(getNowStrDate())
    }

    websocket.onerror = function(evt){
        $("#log_content").append("<br><span class=\"error_text\">Connection error ...</span><br>")
        websocket = null
        if(!check_in){
            $("#log_content").scrollTop($("#log_content")[0].scrollHeight);
        }
    }

    websocket.onclose = function(evt){
        $("#log_content").append("<br><span class=\"error_text\">Connection closed ...</span><br>")
        if(!check_in) {
            $("#log_content").scrollTop($("#log_content")[0].scrollHeight);
        }
        websocket = null
    }
}


function close_websocket(){
    if(websocket){
        websocket.close()
    }
}

function clear_log_content(){
    $("#log_content").empty()
    window_lines = 0;
    highlight_lines = 0;
    $("#window_lines").text(window_lines)
    $("#highlight_lines").text(highlight_lines)
}