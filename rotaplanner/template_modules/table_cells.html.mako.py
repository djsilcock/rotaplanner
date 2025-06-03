# -*- coding:utf-8 -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
STOP_RENDERING = runtime.STOP_RENDERING
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 10
_modified_time = 1748815535.5924473
_enable_loop = True
_template_filename = 'rotaplanner/templates/table_cells.html.mako'
_template_uri = 'table_cells.html.mako'
_source_encoding = 'utf-8'
_exports = ['show_toasts', 'render_cell', 'cell_stream']



import json


def render_body(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        def cell_stream(replacement_cells,grid_type):
            return render_cell_stream(context._locals(__M_locals),replacement_cells,grid_type)
        grid_type = context.get('grid_type', UNDEFINED)
        replacement_cells = context.get('replacement_cells', UNDEFINED)
        __M_writer = context.writer()
        __M_writer('\r\n\r\n')
        __M_writer('\r\n\r\n')
        __M_writer('\r\n\r\n')
        __M_writer('\r\n\r\n<turbo-stream target="context-menu" action="update"><template></template></turbo-stream>\r\n')
        __M_writer(str(cell_stream(replacement_cells, grid_type)))
        __M_writer('\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_show_toasts(context,toasts):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_writer = context.writer()
        __M_writer('\r\n<script>\r\n')
        for t in toasts:
            __M_writer('  $.toast(')
            __M_writer(str(json.dumps(t)))
            __M_writer(')\r\n')
        __M_writer('</script>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_render_cell(context,cell):
    __M_caller = context.caller_stack._push_frame()
    try:
        grid_type = context.get('grid_type', UNDEFINED)
        str = context.get('str', UNDEFINED)
        __M_writer = context.writer()
        __M_writer('\r\n<div class="inner-cell" id="inner-')
        __M_writer(str(cell.cell_id))
        __M_writer('">\r\n')
        for activity in cell.activities:
            __M_writer('    <div class="activity" draggable="true" data-activity-id="')
            __M_writer(str(activity.activity_id))
            __M_writer('">\r\n      <div class="activity-name">')
            __M_writer(str(activity.name))
            __M_writer('</div>\r\n')
            if activity.location_id is not None and str(activity.location_id) not in str(cell.cell_id):
                __M_writer('        <div class="location">')
                __M_writer(str(activity.location_name))
                __M_writer('</div>\r\n')
            for sa in activity.staff_assignments:
                pass
                if str(sa.staff_id) not in str(cell.cell_id):
                    __M_writer('          <div class="staff-allocation" ')
                    __M_writer(str('draggable="true"' if grid_type=="location" else ""))
                    __M_writer(' data-staff-id="')
                    __M_writer(str(sa.staff_id))
                    __M_writer('">')
                    __M_writer(str(sa.staff_name))
                    __M_writer('</div>\r\n')
            __M_writer('    </div>\r\n')
        __M_writer('</div>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_cell_stream(context,replacement_cells,grid_type):
    __M_caller = context.caller_stack._push_frame()
    try:
        def render_cell(cell):
            return render_render_cell(context,cell)
        __M_writer = context.writer()
        __M_writer('\r\n')
        for cell in replacement_cells:
            __M_writer('  <turbo-stream action="replace" target="inner-')
            __M_writer(str(cell.cell_id))
            __M_writer('">\r\n    <template>\r\n      ')
            __M_writer(str(render_cell(cell)))
            __M_writer('\r\n    </template>\r\n  </turbo-stream>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


"""
__M_BEGIN_METADATA
{"filename": "rotaplanner/templates/table_cells.html.mako", "uri": "table_cells.html.mako", "source_encoding": "utf-8", "line_map": {"16": 1, "17": 2, "18": 3, "19": 4, "20": 0, "29": 3, "30": 11, "31": 29, "32": 39, "33": 42, "34": 42, "40": 5, "44": 5, "45": 7, "46": 8, "47": 8, "48": 8, "49": 10, "55": 13, "61": 13, "62": 14, "63": 14, "64": 15, "65": 16, "66": 16, "67": 16, "68": 17, "69": 17, "70": 18, "71": 19, "72": 19, "73": 19, "74": 21, "76": 22, "77": 23, "78": 23, "79": 23, "80": 23, "81": 23, "82": 23, "83": 23, "84": 26, "85": 28, "91": 31, "97": 31, "98": 32, "99": 33, "100": 33, "101": 33, "102": 35, "103": 35, "109": 103}}
__M_END_METADATA
"""
