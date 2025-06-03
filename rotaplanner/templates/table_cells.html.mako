<%!
import json
%>

<%def name="show_toasts(toasts)">
<script>
% for t in toasts:
  $.toast(${json.dumps(t)})
% endfor
</script>
</%def>

<%def name="render_cell(cell)">
<div class="inner-cell" id="inner-${cell.cell_id}">
  % for activity in cell.activities:
    <div class="activity" draggable="true" data-activity-id="${activity.activity_id}">
      <div class="activity-name">${activity.name}</div>
      % if activity.location_id is not None and str(activity.location_id) not in str(cell.cell_id):
        <div class="location">${activity.location_name}</div>
      % endif
      % for sa in activity.staff_assignments:
        % if str(sa.staff_id) not in str(cell.cell_id):
          <div class="staff-allocation" ${'draggable="true"' if grid_type=="location" else ""} data-staff-id="${sa.staff_id}">${sa.staff_name}</div>
        % endif
      % endfor
    </div>
  % endfor
</div>
</%def>

<%def name="cell_stream(replacement_cells, grid_type)">
% for cell in replacement_cells:
  <turbo-stream action="replace" target="inner-${cell.cell_id}">
    <template>
      ${render_cell(cell)}
    </template>
  </turbo-stream>
% endfor
</%def>

<turbo-stream target="context-menu" action="update"><template></template></turbo-stream>
${cell_stream(replacement_cells, grid_type)}
