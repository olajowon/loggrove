/**
 * Created by zhouwang on 2018/5/23.
 */


function logfile_read(){
    $("#log_content_row").show()
    $(".error_text").empty()
    form_obj = $("#logfile_form")
    total_pages = null;
    total_lines = null;
    match_lines = null;
    page = null;
    logfile = form_obj.find("input[name='logfile']").val()
    match = form_obj.find("input[name='match']").val()
    path = form_obj.find("select[name='path']").val()
    host = form_obj.find("select[name='host']").val()
    filter_search_line = form_obj.find("input[name='filter_search_line']:checked").val()
    get_log_content(1)
    return false;
}

function get_log_content(p){
    if(p == page){
        return false;
    }
    $("#log_content").html("Reading...")
    $("#paging").empty()
    $(".error_text").empty()
    if(p==1){
        $("#total_lines").text("--")
        $("#match_lines").text("--")
    }
    $("#page").text("--")
    $("#total_pages").text("--")
    $("#highlight_lines").text("--")
    $("#lines").text("--")

    if(filter_search_line){
        var request_data = {"page":p, "logfile": logfile, "match": match, "path": path, "host": host, "clean": true}
    }else{
        var request_data = {"page":p, "logfile": logfile, "match": match, "path": path, "host": host, "clean": false}
    }

    var posit = "head"
    if (total_pages && total_pages > 0) {
        posit = p < (total_pages / 2) ? "head" : "tail"
    }
    request_data['posit'] = posit

    $.ajax({
        url:"/read/",
        type:"GET",
        data: request_data,
        success:function(result){
            var response_data = jQuery.parseJSON(result)
            var search_result = log_content_searching(response_data["data"]["contents"], match)
            total_lines = response_data["data"]["total_lines"] == null ? total_lines : response_data["data"]["total_lines"];
            match_lines = response_data["data"]["match_lines"] == null ? match_lines : response_data["data"]["match_lines"];
            page = response_data["data"]["page"]
            total_pages = response_data["data"]["total_pages"] == null ? total_pages : response_data["data"]["total_pages"];
            lines = response_data["data"]["lines"]

            $("#log_content").html(search_result["log_content"])
            $("#total_lines").text(total_lines)
            $("#match_lines").text(match_lines)
            $("#highlight_lines").text(search_result["highlight_lines"])
            $("#lines").text(lines)
            $("#page").text(page)
            $("#total_pages").text(total_pages)
            if (total_pages > 0){
                $("#paging").html(log_content_paging())
            }
        },
        error:function(result){
            if (result.status != 0) {
                var response_data = jQuery.parseJSON(result.responseText)
                if (response_data["code"] == 400) {
                    for (var k in response_data["error"]) {
                        form_obj.find("[name='"+ k +"_error']").text(response_data["error"][k])
                    }
                }
                $("#log_content").html(
                    '<div class="alert alert-danger">' +
                    '<i class="fa fa-times"></i> ' + response_data["msg"] +
                    '</div>'
                )
            }else{
                $("#log_content").html(
                    '<div class="alert alert-danger">' +
                    '<i class="fa fa-times"></i> HTTP: 0 ' + result.statusText +
                    '</div>'
                )
            }
        }
    })
}


function log_path(path, nodes){
    var paths = []
    for(var i=0;i<nodes.length;i++){
        if(nodes[i].hasOwnProperty('nodes')){
            paths = paths.concat(log_path(path+'/'+nodes[i]["text"], nodes[i]["nodes"]))
        }else{
            paths.push(path+'/'+nodes[i]["text"])
        }
    }
    return paths
}

function log_content_paging(){
    var page_range = []
    for(var i=2;i>0;i--){
        if(page-i>=1){
            page_range.push(page-i)
        }
    }
    page_range.push(page)
    for(var i=1;i<5;i++){
        if(page+i<=total_pages){
            page_range.push(page+i)
        }
    }
    if(language == "cn"){
        var page_li = '<li class="'+ (page==1?'disabled':'') +'"><span onclick="get_log_content(1)">首页</span></li>' +
                    '<li class="'+ (page==1?'disabled':'') +'"><span onclick="get_log_content('+ (page-1) +')">上一页</span></li>'

        for(var i=0; i<page_range.length;i++){
            page_li += '<li class="'+ (page_range[i]==page?'active':'') +'"><span onclick="get_log_content('+ (page_range[i]) +')">'+ page_range[i] +'</span></li>'
        }

        page_li += '<li class="'+ (page==total_pages?'disabled':'') +'"><span onclick="get_log_content('+ (page+1) +')">下一页</span></li>' +
            '<li class="'+ (page==total_pages?'disabled':'') +'"><span onclick="get_log_content('+ total_pages +')">尾页</span></li>'

        var page_html = '<ul class="pagination" style="margin-top: 0px">' + page_li + '</ul>' +
            '<div style="clear: both">' +
                '<div class="form-group" style="display:inline; clear: both">' +
                    '<div style="display:inline-block">' +
                    '<span class="text-primary" style="font-size: 14px; height: 25px">第 ' + page +' 页, 共 ' + total_pages +' 页 &nbsp;</span>' +
                    '</div>' +
                    '<div style="display:inline-block">' +
                        '<input type="text" class="form-control input-sm" id="skip_page" style="padding:5px; width:50px;" autocomplete="off"/>' +
                    '</div>' +
                    '<div style="display:inline-block">' +
                        '<button type="button" class="text-primary" onclick="get_log_content($(\'#skip_page\').val())" style="border: 0px; background: none; font-size: 14px; height: 25px">跳转</button>' +
                    '</div>' +
                '</div>' +
            '</div>'
    }else{
        var page_li = '<li class="'+ (page==1?'disabled':'') +'"><span onclick="get_log_content(1)">&laquo;</span></li>' +
                    '<li class="'+ (page==1?'disabled':'') +'"><span onclick="get_log_content('+ (page-1) +')">&lsaquo;</span></li>'

        for(var i=0; i<page_range.length;i++){
            page_li += '<li class="'+ (page_range[i]==page?'active':'') +'"><span onclick="get_log_content('+ (page_range[i]) +')">'+ page_range[i] +'</span></li>'
        }

        page_li += '<li class="'+ (page==total_pages?'disabled':'') +'"><span onclick="get_log_content('+ (page+1) +')">&rsaquo;</span></li>' +
            '<li class="'+ (page==total_pages?'disabled':'') +'"><span onclick="get_log_content('+ total_pages +')">&raquo;</span></li>'

        var page_html = '<ul class="pagination" style="margin-top: 0px">' + page_li + '</ul>' +
            '<div style="clear: both">' +
                '<div class="form-group" style="display:inline; clear: both">' +
                    '<div style="display:inline-block">' +
                    '<span class="text-primary" style="font-size: 14px; height: 25px">Showing ' + page +' pages, total ' + total_pages +' pages &nbsp;</span>' +
                    '</div>' +
                    '<div style="display:inline-block">' +
                        '<input type="text" class="form-control input-sm" id="skip_page" style="padding:5px; width:50px;" autocomplete="off"/>' +
                    '</div>' +
                    '<div style="display:inline-block">' +
                        '<button type="button" class="text-primary" onclick="get_log_content($(\'#skip_page\').val())" style="border: 0px; background: none; font-size: 14px; height: 25px">skip</button>' +
                    '</div>' +
                '</div>' +
            '</div>'
    }
    return page_html
}
