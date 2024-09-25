import functools
import contextlib
import re
import html

class TextNode:
    def __init__(self,text):
        self.content=text
    def render(self,indent,cur_indent):
        yield f"{' '*cur_indent}{self.content}"



class HTMLElement:
    def __init__(self,tagname,*tags,**attributes):
        self._taglist=[]
        for t in tags+attributes.get('children',[]):
            if isinstance(t,str):
                self._taglist.append(TextNode(t))
            elif isinstance(t,HTMLElement):
                self._taglist.append(t)
            elif t is None:
                continue
            else:
                raise TypeError
        self._tagname=tagname
        self._attributes={}
        for attrib,val in attributes.items():
            if val not in (True,False,None):
                val=(html.escape(str(val),True)
                     .replace('_','-'))
            attrib=attrib.strip('_').replace('_','-')
            self._attributes[attrib]=val
    def text(self,text):
        self._taglist.append(TextNode(text))
    def append(self,node):
        self._taglist.append(node)
    def render(self,indent=0,cur_indent=0):
        attributes=[]
        for attrib,value in self._attributes.items():
            if value is None or value==False:
                continue
            if value == True:
                attributes.append(attrib)
            else:
                attributes.append(f'{attrib}={value}')
        space=" "*cur_indent
        yield f"{space}<{self._tagname} {' '.join(attributes)}>"
        for el in self._taglist:
            yield from el.render(indent,cur_indent+indent)
        yield f"{space}</{self._tagname}>"
    def __getattr__(self,tagname):
        def new_element(*tags,**attributes):
            new_node=HTMLElement(tagname,*tags,**attributes)
            self._taglist.append(new_node)
            return new_node
        return new_element
    





def activity(activity_def,staff_id=None,show_location=True):
    activitydiv=HTMLElement('div',
        _class=activity, 
        data_staff=staff_id, 
        data_activityid=activity_def.activity_id, 
        data_activitydate=activity_def.activity_start.date().isoformat(), 
        draggable="true")
    activitydiv.div(activity_def.name,_class="activity-name")
    activitydiv.div(activity_def.location,_class="activity-location")
    for assignment in activity_def.staff_assignments:
        if assignment.staff.id != staff_id:
            assignmentdiv=activitydiv.div(_class='assignment')
            assignmentdiv.text(assignment.staff.name)
            if (assignment.start_time is not None) and (assignment.finish_time is not None):
                assignmentdiv.text(f"{assignment.start_time.strftime('%H')}-{assignment.finish_time.strftime('%H')}")
        
def activitycell(date,staffmember,as_template=False):
    tablecell=HTMLElement('td', _class='activitycell', data_date=date.isoformat(), data_staff=staffmember.id, _id=f"td-{{date.isoformat()}}-{{staffmember.id}}")
    for act in activities[date]:
        if act.includes_staff(staffmember.id):
            tablecell.append(activity(act,staff_id=staffmember.id))
    if as_template:
        return HTMLElement('template', tablecell,_id=f"td-{date.isoformat()}-{staffmember.id}")
    return tablecell
    

structure=HTMLElement('html',
                HTMLElement('body',
                                  HTMLElement('div')))

<!DOCTYPE html>
<html>
<head>
<link rel=stylesheet href="/static/table.css"/>
<script src="/static/table.js" ></script>
</head>
<body>

<div id="rota-table">
<table>
<thead>
<tr>
<th></th>
{% for date in dates %}
<th class="column-header">{{date.strftime('%d %b')}}</th>
{% endfor %}
</tr>
</thead>
<tbody id="rota-table-content">
{% for staffmember in staff %}
    <tr>
        <td class=rowheader>{{staffmember.name}}</td>
        {% for date in dates %}
        {{activitycell(date=date,staffmember=staffmember,as_template=as_template)}}
        {% endfor %}
    </tr>
{% endfor%}
<tr>
<td><span id=empty></span></td>
{% for date in dates %}
    <td data-date={{date.isoformat()}} class="unallocated-activities" id="td-{{date.isoformat()}}-unalloc">
    {% for act in activities[date] %}
        {{activity(act)}}
    {% endfor %}
    </td>
{% endfor %}
</tr>
</tbody>
</table>
</div>
</body>
</html>

print ("\n".join(document.render(2)))
'''