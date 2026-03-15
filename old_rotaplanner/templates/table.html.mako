<%inherit file="layout.html"/>


<%block name="title">View by name</%block>
<%namespace name="cells" file="table_cells.html.mako"/>

<%block name="assets">
<link rel="stylesheet" href="/static/table.css" />
<script src="/static/table.js"></script>
</%block>

<%block name="main">
<main>
  <table id="rota-table" data-turbo-prefetch="false">
    <thead>
      <tr>
        <th></th>
        % for d in dates:
          <th class="day-header" data-date="${d}">${d}</th>
        % endfor
      </tr>
    </thead>
    <tbody>
      % for staff_or_location in y_axis.values():
        <tr>
          <td class="row-header">${staff_or_location.name}</td>
          % for d in dates:
            <% cell = activity_cells[(d, staff_or_location.id)] %>
            <td 
              class="day-cell" 
              id="${cell.cell_id}" 
              data-date="${d}" 
              data-${grid_type}="${str(staff_or_location.id)}" 
              style="anchor-name:--${cell.cell_id}">
              ${cells.render_cell(cell)}
            </td>
          % endfor
        </tr>
      % endfor
      <tr>
        <td class="row-header">Unallocated</td>
        % for d in dates:
          <td class="day-cell" id="cell-${d}-None" data-date="${d}">
            ${cells.render_cell(activity_cells[(d, "None")])}
          </td>
        % endfor
      </tr>
    </tbody>
  </table>
  <div id="context-menu"></div>
  <div id="activity-dialog"></div>
</main>
</%block>
