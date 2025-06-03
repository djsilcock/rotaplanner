# -*- coding:utf-8 -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
STOP_RENDERING = runtime.STOP_RENDERING
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 10
_modified_time = 1748815793.3120081
_enable_loop = True
_template_filename = 'rotaplanner/templates/table_context_menu.html.mako'
_template_uri = 'table_context_menu.html.mako'
_source_encoding = 'utf-8'
_exports = []


def render_body(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        activity_form = context.get('activity_form', UNDEFINED)
        location = context.get('location', UNDEFINED)
        staff = context.get('staff', UNDEFINED)
        date = context.get('date', UNDEFINED)
        str = context.get('str', UNDEFINED)
        __M_writer = context.writer()
        __M_writer('<turbo-stream target="context-menu" action="replace">  \r\n<template>\r\n<div id="context-menu" style="position-anchor: --cell-')
        __M_writer(str(date))
        __M_writer(str(('-' + str(staff)) if staff else ''))
        __M_writer(str(('-' + str(location)) if location else ''))
        __M_writer('">\r\n    <div class="dialog-content">\r\n    <div class="content">\r\n      <form id="add-activity-form" method="post" action="/rota_grid/add_activity">\r\n        ')
        __M_writer(str(activity_form.staff))
        __M_writer('\r\n        ')
        __M_writer(str(activity_form.location))
        __M_writer('\r\n        ')
        __M_writer(str(activity_form.date))
        __M_writer('\r\n')
        for opt in activity_form.existing_activity:
            __M_writer('        <div class="context-menu-option">\r\n        <button type="submit" name="')
            __M_writer(str(activity_form.existing_activity.name))
            __M_writer('" value="')
            __M_writer(str(opt.data))
            __M_writer('">\r\n')
            if opt.data == "--new--":
                __M_writer('          Create new activity\r\n')
            elif staff:
                __M_writer('          Allocate to ')
                __M_writer(str(opt.label.text))
                __M_writer('\r\n')
            elif location:
                __M_writer('          Move ')
                __M_writer(str(opt.label.text))
                __M_writer(' here\r\n')
            __M_writer('        </button> \r\n        </div>\r\n')
        __M_writer('        \r\n      </form>\r\n      \r\n    </div>\r\n    \r\n    \r\n    </div>  \r\n</div>\r\n</template>\r\n</turbo-stream>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


"""
__M_BEGIN_METADATA
{"filename": "rotaplanner/templates/table_context_menu.html.mako", "uri": "table_context_menu.html.mako", "source_encoding": "utf-8", "line_map": {"16": 0, "26": 1, "27": 3, "28": 3, "29": 3, "30": 3, "31": 7, "32": 7, "33": 8, "34": 8, "35": 9, "36": 9, "37": 10, "38": 11, "39": 12, "40": 12, "41": 12, "42": 12, "43": 13, "44": 14, "45": 15, "46": 16, "47": 16, "48": 16, "49": 17, "50": 18, "51": 18, "52": 18, "53": 20, "54": 23, "60": 54}}
__M_END_METADATA
"""
