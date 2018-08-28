/**
 * Bootstrap Table Chinese translation
 * Author: Zhixin Wen<wenzhixin2010@gmail.com>
 */
(function ($) {
    'use strict';

    $.fn.bootstrapTable.locales['zh-CN'] = {
        formatLoadingMessage: function () {
            return '加载数据中，请稍等...';
        },
        formatRecordsPerPage: function (pageNumber) {
            return '每页 ' + pageNumber + ' 条';
        },
        formatShowingRows: function (pageFrom, pageTo, totalRows) {
            return '第 ' + pageFrom + ' 至 ' + pageTo + ' 条，共 ' + totalRows + ' 条。';
        },
        formatSearch: function () {
            return '搜索...';
        },
        formatNoMatches: function () {
            return '无相关数据';
        },
        formatPaginationSwitch: function () {
            return '隐藏/显示分页';
        },
        formatRefresh: function () {
            return '刷新';
        },
        formatToggle: function () {
            return '切换';
        },
        formatColumns: function () {
            return '列';
        },
        formatExport: function () {
            return '导出数据';
        },
        formatClearFilters: function () {
            return '清空过滤';
        }
    };

    $.extend($.fn.bootstrapTable.defaults, $.fn.bootstrapTable.locales['zh-CN']);

})(jQuery);
