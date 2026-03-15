# -*- coding:utf-8 -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
STOP_RENDERING = runtime.STOP_RENDERING
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 10
_modified_time = 1748815337.358248
_enable_loop = True
_template_filename = 'rotaplanner/templates/layout.html'
_template_uri = 'layout.html'
_source_encoding = 'utf-8'
_exports = ['title', 'assets', 'main']


def render_body(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        self = context.get('self', UNDEFINED)
        def main():
            return render_main(context._locals(__M_locals))
        def title():
            return render_title(context._locals(__M_locals))
        def assets():
            return render_assets(context._locals(__M_locals))
        __M_writer = context.writer()
        __M_writer('<!DOCTYPE html>\r\n<html>\r\n  <head>\r\n    <script\r\n      type="module"\r\n      src="https://cdn.jsdelivr.net/npm/@hotwired/turbo@latest/dist/turbo.es2017-esm.min.js"\r\n    ></script>\r\n    <script src="/static/common.js"></script>\r\n    <link rel="stylesheet" href="/static/common.css" />\r\n    <title>\r\n      ')
        if 'parent' not in context._data or not hasattr(context._data['parent'], 'title'):
            context['self'].title(**pageargs)
        

        __M_writer('\r\n    </title>\r\n    ')
        if 'parent' not in context._data or not hasattr(context._data['parent'], 'assets'):
            context['self'].assets(**pageargs)
        

        __M_writer('\r\n  </head>\r\n\r\n  <body>\r\n    <div class="ui sidebar inverted vertical menu left">\r\n      <nav class="ui inverted vertical menu">\r\n        <a class="item" href="/rota-grid/staff/grid">Rota by person</a>\r\n        <a class="item" href="/rota-grid/location/grid">Rota by location</a>\r\n\r\n        <a class="item" href="">Manage activity templates</a>\r\n        <a class="item" href="/api/templates/supply">Manage supply templates</a>\r\n        <a class="item" href="/api/activities/table">Rota solver</a>\r\n        <a class="item" href="/api/templates/supply">Import from CLW</a>\r\n        <a class="item" href="/api/config">Setup staff</a>\r\n      </nav>\r\n      <button slot="footer" variant="primary">Close</button>\r\n    </div>\r\n    <div class="pusher">\r\n      <div class="header">\r\n        <button>\r\n          <sl-icon name="layout-text-sidebar-reverse" id="menubutton"></sl-icon>\r\n        </button>\r\n        ')
        __M_writer(str(self.title()))
        __M_writer('\r\n      </div>\r\n      ')
        if 'parent' not in context._data or not hasattr(context._data['parent'], 'main'):
            context['self'].main(**pageargs)
        

        __M_writer('\r\n      <hr />\r\n      <div id="additional"></div>\r\n    </div>\r\n    <script>\r\n      const menuButton = document.getElementById("menubutton");\r\n      const drawer = document.querySelector("sl-drawer");\r\n      menuButton.addEventListener("click", () => {\r\n        drawer.show();\r\n      });\r\n    </script>\r\n  </body>\r\n</html>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_title(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        def title():
            return render_title(context)
        __M_writer = context.writer()
        __M_writer('Rotaplanner')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_assets(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        def assets():
            return render_assets(context)
        __M_writer = context.writer()
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_main(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        def main():
            return render_main(context)
        __M_writer = context.writer()
        __M_writer(' ... ')
        return ''
    finally:
        context.caller_stack._pop_frame()


"""
__M_BEGIN_METADATA
{"filename": "rotaplanner/templates/layout.html", "uri": "layout.html", "source_encoding": "utf-8", "line_map": {"16": 0, "28": 1, "33": 11, "38": 13, "39": 35, "40": 35, "45": 37, "51": 11, "57": 11, "63": 13, "74": 37, "80": 37, "86": 80}}
__M_END_METADATA
"""
