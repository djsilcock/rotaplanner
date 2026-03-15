# -*- coding:utf-8 -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
STOP_RENDERING = runtime.STOP_RENDERING
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 10
_modified_time = 1748899777.84534
_enable_loop = True
_template_filename = 'rotaplanner/templates/edit_activity_template.html.mako'
_template_uri = 'edit_activity_template.html.mako'
_source_encoding = 'utf-8'
_exports = ['ordinal_options', 'render_linklike', 'form_line', 'render_group', 'render_rule', 'datetime_field', 'requirement_form', 'new_requirement_form', 'main']



    # Helper for ordinal (1st, 2nd, etc.)
def ordinal(n):
    return "%d%s" % (n, "tsnrhtdd"[(n//10 % 10!=1)*(n%10<4)*n%10::4])


def render_body(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        loop = __M_loop = runtime.LoopStack()
        def main():
            return render_main(context._locals(__M_locals))
        def form_line(field):
            return render_form_line(context._locals(__M_locals),field)
        form = context.get('form', UNDEFINED)
        def requirement_form(req,initially_open=False):
            return render_requirement_form(context._locals(__M_locals),req,initially_open)
        __M_writer = context.writer()
        __M_writer('\r\n\r\n')
        __M_writer('\r\n\r\n')
        __M_writer('\r\n\r\n')
        __M_writer('\r\n\r\n')
        __M_writer('\r\n\r\n')
        __M_writer('\r\n\r\n')
        __M_writer('\r\n\r\n')
        __M_writer('\r\n\r\n')
        __M_writer('\r\n\r\n')
        if 'parent' not in context._data or not hasattr(context._data['parent'], 'main'):
            context['self'].main(**pageargs)
        

        return ''
    finally:
        context.caller_stack._pop_frame()


def render_ordinal_options(context,first,last,name,value):
    __M_caller = context.caller_stack._push_frame()
    try:
        range = context.get('range', UNDEFINED)
        __M_writer = context.writer()
        __M_writer('\r\n')
        for index in range(first, last+1):
            __M_writer('<option value="')
            __M_writer(str(index))
            __M_writer('" ')
            __M_writer(str("selected" if index==value else ""))
            __M_writer('>\r\n')
            if index==1:
                __M_writer('        Every ')
                __M_writer(str(name))
                __M_writer('\r\n')
            else:
                __M_writer('        Every ')
                __M_writer(str(ordinal(index)))
                __M_writer(' ')
                __M_writer(str(name))
                __M_writer('\r\n')
            __M_writer('</option>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_render_linklike(context,field):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_writer = context.writer()
        __M_writer('\r\n<label class="linklike">\r\n    ')
        __M_writer(str(field(**{'up-validate':True})))
        __M_writer(str(field.label.text))
        __M_writer('\r\n</label>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_form_line(context,field):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_writer = context.writer()
        __M_writer('\r\n<div id="')
        __M_writer(str(field.id))
        __M_writer('-group" class="field">\r\n')
        if field.errors:
            __M_writer('        <div class="ui negative message">\r\n')
            for err in field.errors:
                __M_writer('            <div>')
                __M_writer(str(err))
                __M_writer('</div>\r\n')
            __M_writer('        </div>\r\n')
        __M_writer('    ')
        __M_writer(str(field))
        __M_writer('\r\n</div>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_render_group(context,group,rule_types,is_root=False):
    __M_caller = context.caller_stack._push_frame()
    try:
        def render_group(group,rule_types,is_root=False):
            return render_render_group(context,group,rule_types,is_root)
        def render_rule(rule,rule_types):
            return render_render_rule(context,rule,rule_types)
        len = context.get('len', UNDEFINED)
        __M_writer = context.writer()
        __M_writer('\r\n<li>\r\n    <div id="')
        __M_writer(str(group._prefix))
        __M_writer('-container" class="rule-box">\r\n        ')
        __M_writer(str(group.group_type))
        __M_writer('\r\n        <a href="">Add rule</button>\r\n        <label class="linklike">')
        __M_writer(str(group.should_add_group))
        __M_writer('Add rule group</label>\r\n')
        if not is_root:
            __M_writer('            <button type="button" class="delete-group">Delete group</button>\r\n')
        __M_writer('        <ul id="')
        __M_writer(str(group._prefix))
        __M_writer('-groups">\r\n')
        for subgroup in group.groups:
            __M_writer('                ')
            __M_writer(str(render_group(subgroup, rule_types)))
            __M_writer('\r\n')
        __M_writer('            </ul>\r\n        <ul id="')
        __M_writer(str(group._prefix))
        __M_writer('-rules">\r\n')
        for rule in group.rules:
            __M_writer('                ')
            __M_writer(str(render_rule(rule, rule_types)))
            __M_writer('\r\n')
        __M_writer('            </ul>   \r\n')
        if len(group.groups) == 0 and len(group.rules) == 0:
            __M_writer('                ⚠️This group has no members\r\n')
        __M_writer('        \r\n    </div>\r\n</li>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_render_rule(context,rule,rule_types):
    __M_caller = context.caller_stack._push_frame()
    try:
        req = context.get('req', UNDEFINED)
        __M_writer = context.writer()
        __M_writer('\r\n<li>\r\n    <details class="rule-definition" ')
        __M_writer(str("open" if req.is_open.data else "" ))
        __M_writer(' name="rule-definition-box">\r\n        <summary class="description">(rule description)</summary>\r\n        <div style="display:none">')
        __M_writer(str(rule.is_open))
        __M_writer('</div>\r\n        <table class="rule-box">\r\n            <tbody>\r\n                ')
        __M_writer(str(rule.rule_type))
        __M_writer('\r\n                ')
        __M_writer(str(rule.day_interval))
        __M_writer('\r\n                ')
        __M_writer(str(rule.week_interval))
        __M_writer('\r\n                ')
        __M_writer(str(rule.month_interval))
        __M_writer('\r\n                ')
        __M_writer(str(rule.start_date))
        __M_writer('\r\n                ')
        __M_writer(str(rule.finish_date))
        __M_writer('\r\n                ')
        __M_writer(str(rule.tag))
        __M_writer('\r\n                ')
        __M_writer(str(rule.date_type))
        __M_writer('\r\n            </tbody>\r\n        </table>\r\n    </details>\r\n</li>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_datetime_field(context,field):
    __M_caller = context.caller_stack._push_frame()
    try:
        __M_writer = context.writer()
        __M_writer('\r\n<div class="field">\r\n')
        __M_writer(str(field.label))
        __M_writer('\r\n<div class="ui calendar" id="')
        __M_writer(str(field.id))
        __M_writer('">\r\n    <div class="ui input left icon">\r\n        <input type="text" name="')
        __M_writer(str(field.name))
        __M_writer('" placeholder="')
        __M_writer(str(field.label.text))
        __M_writer('">\r\n        <i class="time icon"></i>\r\n    </div>\r\n</div>\r\n</div>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_requirement_form(context,req,initially_open=False):
    __M_caller = context.caller_stack._push_frame()
    try:
        def form_line(field):
            return render_form_line(context,field)
        __M_writer = context.writer()
        __M_writer('\r\n\r\n<details ')
        __M_writer(str("open" if initially_open else "" ))
        __M_writer('>\r\n                        <summary>Requirement  <button type=button>Remove</button></summary>\r\n                    \r\n                        <table class="requirement">\r\n                            <div style="display:none">')
        __M_writer(str(req.is_open))
        __M_writer('</div>\r\n                            ')
        __M_writer(str(form_line(req.skills)))
        __M_writer('\r\n                            ')
        __M_writer(str(form_line(req.requirement)))
        __M_writer('\r\n                            ')
        __M_writer(str(form_line(req.optional)))
        __M_writer('\r\n                            ')
        __M_writer(str(form_line(req.attendance)))
        __M_writer('\r\n                            ')
        __M_writer(str(form_line(req.geofence)))
        __M_writer('\r\n                        </table>\r\n                    </details>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_new_requirement_form(context,old_ref,new_ref,req):
    __M_caller = context.caller_stack._push_frame()
    try:
        def requirement_form(req,initially_open=False):
            return render_requirement_form(context,req,initially_open)
        __M_writer = context.writer()
        __M_writer('\r\n    <turbo-stream target="addafter-')
        __M_writer(str(old_ref))
        __M_writer('" action="replace">\r\n    <template>\r\n        ')
        __M_writer(str(requirement_form(req,initially_open=True)))
        __M_writer('\r\n        <a id="addafter-')
        __M_writer(str(new_ref))
        __M_writer('" data-turbo-stream href="/edit_activity_add_requirement?after=')
        __M_writer(filters.url_escape(str(new_ref)))
        __M_writer('">Add a new requirement after ')
        __M_writer(str(new_ref))
        __M_writer('</a>\r\n    </template>\r\n</turbo-stream>\r\n\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_main(context,**pageargs):
    __M_caller = context.caller_stack._push_frame()
    try:
        loop = __M_loop = runtime.LoopStack()
        def main():
            return render_main(context)
        def form_line(field):
            return render_form_line(context,field)
        form = context.get('form', UNDEFINED)
        def requirement_form(req,initially_open=False):
            return render_requirement_form(context,req,initially_open)
        __M_writer = context.writer()
        __M_writer('\r\n<turbo-stream target="context-menu" action="update"><template></template></turbo-stream>\r\n<turbo-stream target="activity-dialog" action="update"><template>\r\n<div class="dialog-content">\r\n    <form method="post" id="edit-activity-form">\r\n        \r\n        ')
        __M_writer(str(form.activity_id))
        __M_writer('\r\n        <h4>Edit activity</h4>\r\n        <div class="ui form" id="template-editor-settings">\r\n            ')
        __M_writer(str(form_line(form.name)))
        __M_writer('\r\n            ')
        __M_writer(str(form_line(form.start_time)))
        __M_writer('\r\n            ')
        __M_writer(str(form_line(form.finish_time)))
        __M_writer('\r\n            ')
        __M_writer(str(form_line(form.activity_tags)))
        __M_writer('\r\n            ')
        __M_writer(str(form_line(form.location)))
        __M_writer('\r\n            <hr />\r\n            <div id="')
        __M_writer(str(form.requirements.id))
        __M_writer('">\r\n                Requirements:\r\n                <div class="requirement-container">\r\n                    <div class="if-only-child empty-requirements">⚠️No requirements have been set</div>\r\n')
        loop = __M_loop._enter(form.requirements)
        try:
            for req in loop:
                __M_writer('                    ')
                __M_writer(str(requirement_form(req)))
                __M_writer('\r\n')
                if loop.last:
                    __M_writer('                    <a id="addafter-')
                    __M_writer(str(req.name))
                    __M_writer('" data-turbo-stream href="/edit_activity_add_requirement?after=')
                    __M_writer(filters.url_escape(str(req.name)))
                    __M_writer('">Add a new requirement after ')
                    __M_writer(str(req.name))
                    __M_writer('</a>\r\n')
        finally:
            loop = __M_loop._exit()
        __M_writer('                </div>\r\n                \r\n            </div>\r\n        </div>\r\n        <button type="submit">Save template</button>\r\n        </div>\r\n    </form>\r\n    </template>\r\n</turbo-stream>\r\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


"""
__M_BEGIN_METADATA
{"filename": "rotaplanner/templates/edit_activity_template.html.mako", "uri": "edit_activity_template.html.mako", "source_encoding": "utf-8", "line_map": {"16": 1, "17": 2, "18": 3, "19": 4, "20": 5, "21": 6, "22": 0, "35": 5, "36": 17, "37": 23, "38": 36, "39": 63, "40": 84, "41": 96, "42": 112, "43": 122, "53": 7, "58": 7, "59": 8, "60": 9, "61": 9, "62": 9, "63": 9, "64": 9, "65": 10, "66": 11, "67": 11, "68": 11, "69": 12, "70": 13, "71": 13, "72": 13, "73": 13, "74": 13, "75": 15, "81": 19, "85": 19, "86": 21, "87": 21, "88": 21, "94": 25, "98": 25, "99": 26, "100": 26, "101": 27, "102": 28, "103": 29, "104": 30, "105": 30, "106": 30, "107": 32, "108": 34, "109": 34, "110": 34, "116": 38, "125": 38, "126": 40, "127": 40, "128": 41, "129": 41, "130": 43, "131": 43, "132": 44, "133": 45, "134": 47, "135": 47, "136": 47, "137": 48, "138": 49, "139": 49, "140": 49, "141": 51, "142": 52, "143": 52, "144": 53, "145": 54, "146": 54, "147": 54, "148": 56, "149": 57, "150": 58, "151": 60, "157": 65, "162": 65, "163": 67, "164": 67, "165": 69, "166": 69, "167": 72, "168": 72, "169": 73, "170": 73, "171": 74, "172": 74, "173": 75, "174": 75, "175": 76, "176": 76, "177": 77, "178": 77, "179": 78, "180": 78, "181": 79, "182": 79, "188": 86, "192": 86, "193": 88, "194": 88, "195": 89, "196": 89, "197": 91, "198": 91, "199": 91, "200": 91, "206": 98, "212": 98, "213": 100, "214": 100, "215": 104, "216": 104, "217": 105, "218": 105, "219": 106, "220": 106, "221": 107, "222": 107, "223": 108, "224": 108, "225": 109, "226": 109, "232": 114, "238": 114, "239": 115, "240": 115, "241": 117, "242": 117, "243": 118, "244": 118, "245": 118, "246": 118, "247": 118, "248": 118, "254": 124, "266": 124, "267": 130, "268": 130, "269": 133, "270": 133, "271": 134, "272": 134, "273": 135, "274": 135, "275": 136, "276": 136, "277": 137, "278": 137, "279": 139, "280": 139, "281": 143, "284": 144, "285": 144, "286": 144, "287": 145, "288": 146, "289": 146, "290": 146, "291": 146, "292": 146, "293": 146, "294": 146, "297": 149, "303": 297}}
__M_END_METADATA
"""
