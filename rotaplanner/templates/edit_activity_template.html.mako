<%!
    # Helper for ordinal (1st, 2nd, etc.)
    def ordinal(n):
        return "%d%s" % (n, "tsnrhtdd"[(n//10 % 10!=1)*(n%10<4)*n%10::4])
%>

<%def name="ordinal_options(first, last, name, value)">
% for index in range(first, last+1):
<option value="${index}" ${"selected" if index==value else ""}>
    % if index==1:
        Every ${name}
    % else:
        Every ${ordinal(index)} ${name}
    % endif
</option>
% endfor
</%def>

<%def name="render_linklike(field)">
<label class="linklike">
    ${field(**{'up-validate':True})}${field.label.text}
</label>
</%def>

<%def name="form_line(field)">
<div id="${field.id}-group" class="field">
    % if field.errors:
        <div class="ui negative message">
        % for err in field.errors:
            <div>${err}</div>
        % endfor
        </div>
    % endif
    ${field}
</div>
</%def>

<%def name="render_group(group, rule_types, is_root=False)">
<li>
    <div id="${group._prefix}-container" class="rule-box">
        ${group.group_type}
        <a href="">Add rule</button>
        <label class="linklike">${group.should_add_group}Add rule group</label>
        % if not is_root:
            <button type="button" class="delete-group">Delete group</button>
        % endif
        <ul id="${group._prefix}-groups">
            % for subgroup in group.groups:
                ${render_group(subgroup, rule_types)}
            % endfor
            </ul>
        <ul id="${group._prefix}-rules">
            % for rule in group.rules:
                ${render_rule(rule, rule_types)}
            % endfor
            </ul>   
            % if len(group.groups) == 0 and len(group.rules) == 0:
                ⚠️This group has no members
            % endif
        
    </div>
</li>
</%def>

<%def name="render_rule(rule, rule_types)">
<li>
    <details class="rule-definition" ${"open" if req.is_open.data else "" } name="rule-definition-box">
        <summary class="description">(rule description)</summary>
        <div style="display:none">${rule.is_open}</div>
        <table class="rule-box">
            <tbody>
                ${rule.rule_type}
                ${rule.day_interval}
                ${rule.week_interval}
                ${rule.month_interval}
                ${rule.start_date}
                ${rule.finish_date}
                ${rule.tag}
                ${rule.date_type}
            </tbody>
        </table>
    </details>
</li>
</%def>

<%def name="datetime_field(field)">
<div class="field">
${field.label}
<div class="ui calendar" id="${field.id}">
    <div class="ui input left icon">
        <input type="text" name="${field.name}" placeholder="${field.label.text}">
        <i class="time icon"></i>
    </div>
</div>
</div>
</%def>

<%def name="requirement_form(req,initially_open=False)">

<details ${"open" if initially_open else "" }>
                        <summary>Requirement  <button type=button>Remove</button></summary>
                    
                        <table class="requirement">
                            <div style="display:none">${req.is_open}</div>
                            ${form_line(req.skills)}
                            ${form_line(req.requirement)}
                            ${form_line(req.optional)}
                            ${form_line(req.attendance)}
                            ${form_line(req.geofence)}
                        </table>
                    </details>
</%def>

<%def name="new_requirement_form(old_ref,new_ref,req)">
    <turbo-stream target="addafter-${old_ref}" action="replace">
    <template>
        ${requirement_form(req,initially_open=True)}
        <a id="addafter-${new_ref}" data-turbo-stream href="/edit_activity_add_requirement?after=${new_ref|u}">Add a new requirement after ${new_ref}</a>
    </template>
</turbo-stream>

</%def>

<%block name="main">
<turbo-stream target="context-menu" action="update"><template></template></turbo-stream>
<turbo-stream target="activity-dialog" action="update"><template>
<div class="dialog-content">
    <form method="post" id="edit-activity-form">
        
        ${form.activity_id}
        <h4>Edit activity</h4>
        <div class="ui form" id="template-editor-settings">
            ${form_line(form.name)}
            ${form_line(form.start_time)}
            ${form_line(form.finish_time)}
            ${form_line(form.activity_tags)}
            ${form_line(form.location)}
            <hr />
            <div id="${form.requirements.id}">
                Requirements:
                <div class="requirement-container">
                    <div class="if-only-child empty-requirements">⚠️No requirements have been set</div>
                    % for req in form.requirements:
                    ${requirement_form(req)}
                    % if loop.last:
                    <a id="addafter-${req.name}" data-turbo-stream href="/edit_activity_add_requirement?after=${req.name|u}">Add a new requirement after ${req.name}</a>
                    %endif
                    % endfor
                </div>
                
            </div>
        </div>
        <button type="submit">Save template</button>
        </div>
    </form>
    </template>
</turbo-stream>
</%block>