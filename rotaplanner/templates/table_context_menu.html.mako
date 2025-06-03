<turbo-stream target="context-menu" action="replace">  
<template>
<div id="context-menu" style="position-anchor: --cell-${date}${('-' + str(staff)) if staff else ''}${('-' + str(location)) if location else ''}">
    <div class="dialog-content">
    <div class="content">
      <form id="add-activity-form" method="post" action="/rota_grid/add_activity">
        ${activity_form.staff}
        ${activity_form.location}
        ${activity_form.date}
        % for opt in activity_form.existing_activity:
        <div class="context-menu-option">
        <button type="submit" name="${activity_form.existing_activity.name}" value="${opt.data}">
        % if opt.data == "--new--":
          Create new activity
        % elif staff:
          Allocate to ${opt.label.text}
        % elif location:
          Move ${opt.label.text} here
        % endif
        </button> 
        </div>
        % endfor
        
      </form>
      
    </div>
    
    
    </div>  
</div>
</template>
</turbo-stream>
