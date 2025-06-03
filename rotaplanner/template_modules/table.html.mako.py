# -*- coding:utf-8 -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
STOP_RENDERING = runtime.STOP_RENDERING
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 10
_modified_time = 1748892891.2459154
_enable_loop = True
_template_filename = 'rotaplanner/templates/table.html.mako'
_template_uri = 'table.html.mako'
_source_encoding = 'utf-8'
_exports = ['title', 'assets', 'main']


def _mako_get_namespace(context, name):
    try:
        return context.namespaces[(__name__, name)]
    except KeyError:
        _mako_generate_namespaces(context)
        return context.namespaces[(__name__, name)]
def _mako_generate_namespaces(context):
    ns = runtime.TemplateNamespace('cells', context._clean_inheritance_tokens(), templateuri='table_cells.html.mako', callables=None,  calling_uri=_template_uri)
    context.namespaces[(__name__, 'cells')] = ns

def _mako_inherit(template, context):
    _mako_generate_namespaces(context)
    return runtime._inherit_from(context, 'layout.html', _template_uri)
def render_body(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        grid_type = context.get('grid_type', UNDEFINED)
        y_axis = context.get('y_axis', UNDEFINED)
        def title():
            return render_title(context._locals(__M_locals))
        str = context.get('str', UNDEFINED)
        cells = _mako_get_namespace(context, 'cells')
        def main():
            return render_main(context._locals(__M_locals))
        dates = context.get('dates', UNDEFINED)
        def assets():
            return render_assets(context._locals(__M_locals))
        activity_cells = context.get('activity_cells', UNDEFINED)
        __M_writer = context.writer()
        __M_writer('\r\n\r\n\r\n')
        if 'parent' not in context._data or not hasattr(context._data['parent'], 'title'):
            context['self'].title(**pageargs)
        

        __M_writer('\r\n')
        __M_writer('\r\n\r\n')
        if 'parent' not in context._data or not hasattr(context._data['parent'], 'assets'):
            context['self'].assets(**pageargs)
        

        __M_writer('\r\n\r\n')
        if 'parent' not in context._data or not hasattr(context._data['parent'], 'main'):
            context['self'].main(**pageargs)
        

        __M_writer('\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_title(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        def title():
            return render_title(context)
        __M_writer = context.writer()
        __M_writer('View by name')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_assets(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        def assets():
            return render_assets(context)
        __M_writer = context.writer()
        __M_writer('\r\n<link rel="stylesheet" href="/static/table.css" />\r\n<script src="/static/table.js"></script>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_main(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        grid_type = context.get('grid_type', UNDEFINED)
        y_axis = context.get('y_axis', UNDEFINED)
        str = context.get('str', UNDEFINED)
        cells = _mako_get_namespace(context, 'cells')
        def main():
            return render_main(context)
        dates = context.get('dates', UNDEFINED)
        activity_cells = context.get('activity_cells', UNDEFINED)
        __M_writer = context.writer()
        __M_writer('\r\n<main>\r\n  <table id="rota-table" data-turbo-prefetch="false">\r\n    <thead>\r\n      <tr>\r\n        <th></th>\r\n')
        for d in dates:
            __M_writer('          <th class="day-header" data-date="')
            __M_writer(str(d))
            __M_writer('">')
            __M_writer(str(d))
            __M_writer('</th>\r\n')
        __M_writer('      </tr>\r\n    </thead>\r\n    <tbody>\r\n')
        for staff_or_location in y_axis.values():
            __M_writer('        <tr>\r\n          <td class="row-header">')
            __M_writer(str(staff_or_location.name))
            __M_writer('</td>\r\n')
            for d in dates:
                __M_writer('            ')
                cell = activity_cells[(d, staff_or_location.id)] 
                
                __M_writer('\r\n            <td \r\n              class="day-cell" \r\n              id="')
                __M_writer(str(cell.cell_id))
                __M_writer('" \r\n              data-date="')
                __M_writer(str(d))
                __M_writer('" \r\n              data-')
                __M_writer(str(grid_type))
                __M_writer('="')
                __M_writer(str(str(staff_or_location.id)))
                __M_writer('" \r\n              style="anchor-name:--')
                __M_writer(str(cell.cell_id))
                __M_writer('">\r\n              ')
                __M_writer(str(cells.render_cell(cell)))
                __M_writer('\r\n            </td>\r\n')
            __M_writer('        </tr>\r\n')
        __M_writer('      <tr>\r\n        <td class="row-header">Unallocated</td>\r\n')
        for d in dates:
            __M_writer('          <td class="day-cell" id="cell-')
            __M_writer(str(d))
            __M_writer('-None" data-date="')
            __M_writer(str(d))
            __M_writer('">\r\n            ')
            __M_writer(str(cells.render_cell(activity_cells[(d, "None")])))
            __M_writer('\r\n          </td>\r\n')
        __M_writer('      </tr>\r\n    </tbody>\r\n  </table>\r\n  <div id="context-menu"></div>\r\n  <div id="activity-dialog"></div>\r\n</main>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


"""
__M_BEGIN_METADATA
{"filename": "rotaplanner/templates/table.html.mako", "uri": "table.html.mako", "source_encoding": "utf-8", "line_map": {"23": 5, "29": 0, "46": 1, "51": 4, "52": 5, "57": 10, "62": 53, "68": 4, "74": 4, "80": 7, "86": 7, "92": 12, "104": 12, "105": 18, "106": 19, "107": 19, "108": 19, "109": 19, "110": 19, "111": 21, "112": 24, "113": 25, "114": 26, "115": 26, "116": 27, "117": 28, "118": 28, "119": 29, "120": 28, "121": 31, "122": 31, "123": 32, "124": 32, "125": 33, "126": 33, "127": 33, "128": 33, "129": 34, "130": 34, "131": 35, "132": 35, "133": 38, "134": 40, "135": 42, "136": 43, "137": 43, "138": 43, "139": 43, "140": 43, "141": 44, "142": 44, "143": 47, "149": 143}}
__M_END_METADATA
"""
