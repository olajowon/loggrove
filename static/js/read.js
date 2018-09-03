/**
 * Created by zhouwang on 2018/5/23.
 */


function logfile_read(_this){
    $("#log_content_row").show()
    $(".error_text").empty()
    form_obj = $(_this).parent()
    logfile_id = form_obj.find("select[name='logfile_id']").val()
    other_search_pattern = form_obj.find("input[name='other_search_pattern']").val()
    if(other_search_pattern){
        search_pattern = other_search_pattern
    }else{
        search_pattern = form_obj.find("select[name='search_pattern']").val()
    }
    filter_search_line = form_obj.find("input[name='filter_search_line']:checked").val()
    get_log_content(0)
}


function get_log_content(p){
    $("#log_content").html("Reading...")
    $(".error_text").empty()
    $("#total_size").text(0)
    $("#total_lines").text(0)
    $("#size").text(0)
    $("#lines").text(0)
    $("#highlight_lines").text(0)

    if(filter_search_line){
        var request_data = {"page":p, "logfile_id":logfile_id, "search_pattern":search_pattern}
    }else{
        var request_data = {"page":p, "logfile_id":logfile_id}
    }
    $.ajax({
        url:"/read/",
        type:"GET",
        data: request_data,
        success:function(result){
            var response_data = jQuery.parseJSON(result)
            var search_result = log_content_searching(response_data["data"]["contents"], search_pattern)
            $("#log_content").html(search_result["log_content"])

            $("#log_stat_row").show()
            $("#total_size").text((response_data["data"]["total_size"]/1024).toFixed(2))
            $("#total_lines").text(response_data["data"]["total_lines"])
            $("#size").text((response_data["data"]["size"]/1024).toFixed(2))
            $("#lines").text(response_data["data"]["lines"])
            $("#highlight_lines").text(search_result["highlight_lines"])

            page = response_data["data"]["page"]
            total_pages = response_data["data"]["total_pages"]

            $("#paging").html(log_content_paging())
        },
        error:function(result){
            $("#paging").empty()
            $("#log_stat_row").hide()

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