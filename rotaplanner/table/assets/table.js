function watchDraggables(tableElement, aborter, tableType) {
  let droptarget = null;
  let initialTarget = null;
  let draggedElement = null;
  let dragType = null;
  let maybedragging = false;
  let allowedTargetsSelector = null;
  let shiftKey = false;
  let altKey = false;
  let ctrlKey = false;
  let isdragging = false;
  let offsetX = 0;
  let offsetY = 0;
  let ghostElement = null;

  tableElement.addEventListener(
    "pointerdown",
    (event) => {
      if (event.target.closest("[data-not-draggable]")) {
        return;
      }
      if (event.target.closest("[data-draggable]")) {
        maybedragging = true;
        shiftKey = event.shiftKey;
        altKey = event.altKey;
        ctrlKey = event.ctrlKey;
        event.stopPropagation();
      }
      const possibleSelect = event.target.closest("[data-selectable]");

      if (shiftKey) {
        possibleSelect?.classList.toggle("selected");
      } else {
        const selectedElements = tableElement.querySelectorAll(
          "[data-selectable].selected",
        );
        selectedElements.forEach((el) => el.classList.remove("selected"));
        possibleSelect?.classList.add("selected");
      }
    },
    { signal: aborter.signal },
  );

  tableElement.addEventListener(
    "pointermove",
    (event) => {
      const element = event.target.closest("[data-draggable]");

      if (!element) {
        return;
      }
      draggedElement = element;
      dragType = element?.dataset.dragtype ?? null;
      allowedTargetsSelector = element?.dataset.draggable;
      if (maybedragging && !isdragging) {
        initialTarget = element.closest(allowedTargetsSelector);
        ghostElement = element.cloneNode(true);
        draggedElement.dataset.dragging = "true";
        ghostElement.dataset.dragging = "true";
        if (ctrlKey) {
          draggedElement.dataset.ctrldrag = "true";
          ghostElement.dataset.ctrldrag = "true";
        }
        ghostElement.classList.add("ghost");
        document.body.appendChild(ghostElement);
        offsetX = 0;
        offsetY = 0;
        element.setPointerCapture(event.pointerId);
        isdragging = true;
      }
      if (isdragging) {
        offsetX += event.movementX;
        offsetY += event.movementY;
        const droptargets = document.elementsFromPoint(
          event.clientX,
          event.clientY,
        );

        let newdroptarget =
          droptargets.find(
            (el) => el !== element && el.matches(allowedTargetsSelector),
          ) ?? null;
        if (newdroptarget !== droptarget) {
          if (droptarget) {
            delete droptarget.dataset.dragover;
          }
          droptarget = newdroptarget;
          if (droptarget) {
            droptarget.dataset.dragover = "true";
          }
        }
        ghostElement.style.left = `${event.clientX - 10}px`;
        ghostElement.style.top = `${event.clientY - 10}px`;

        if (droptarget) {
          ghostElement.dataset.canDrop = "true";
          draggedElement.dataset.canDrop = "true";
        } else {
          delete ghostElement.dataset.canDrop;
          delete draggedElement.dataset.canDrop;
        }

        // Handle drag move logic here
      }
    },
    { signal: aborter.signal },
  );
  tableElement.addEventListener(
    "pointerup",
    (event) => {
      maybedragging = false;

      if (isdragging) {
        isdragging = false;
        delete ghostElement.dataset.dragging;
        delete ghostElement.dataset.ctrldrag;
        delete ghostElement.dataset.canDrop;
        delete draggedElement.dataset.dragging;
        delete draggedElement.dataset.ctrldrag;
        delete draggedElement.dataset.canDrop;
        draggedElement.releasePointerCapture(event.pointerId);

        if (ghostElement) {
          document.body.removeChild(ghostElement);
          ghostElement = null;
        }
        if (droptarget) {
          delete droptarget.dataset.dragover;
          if (droptarget === initialTarget) {
            return;
          }
          if (dragType === "activity") {
            window.pywebview.api.activity_dropped({
              activityId: draggedElement.dataset.activityId,
              toRowId: droptarget.dataset.rowId,
              toColId: droptarget.dataset.colId,
              fromRowId: initialTarget ? initialTarget.dataset.rowId : null,
              fromColId: initialTarget ? initialTarget.dataset.colId : null,
              shiftKey,
              altKey,
              ctrlKey,
            });
          } else if (dragType === "assignment") {
            window.pywebview.api.assignment_dropped({
              assignmentId: draggedElement.dataset.assignmentId,
              toActivityId: droptarget.dataset.activityId,
              shiftKey,
              altKey,
              ctrlKey,
            });
          }
        }
        draggedElement = null;
      }
    },
    { signal: aborter.signal },
  );
  tableElement.addEventListener(
    "pointercancel",
    (event) => {
      const element = event.target.closest("[data-draggable]");
      if (!element) {
        return;
      }
      if (isdragging) {
        element.dispatchEvent(
          new CustomEvent("drag-cancelled", {
            detail: { target: element, initialTarget },
            bubbles: true,
          }),
        );
      }
      isdragging = false;
      maybedragging = false;
      element.style.transform = "";
      delete element.dataset.dragging;
      delete element.dataset.ctrldrag;
      delete element.dataset.canDrop;
      element.releasePointerCapture(event.pointerId);
    },
    { signal: aborter.signal },
  );
  tableElement.addEventListener(
    "keydown",
    (event) => {
      if (event.key === "Delete") {
        const selectedElements = tableElement.querySelectorAll(
          ".activity.selected.deletable",
        );
        if (selectedElements.length > 0) {
          confirm("Are you sure you want to delete the selected items?") &&
            window.pywebview.api.delete_activities({
              activityIds: Array.from(selectedElements).map((el) => el.id),
            });
        }
      }
    },
    { signal: aborter.signal },
  );
}

function roleChangeListener(tableElement, aborter) {
  tableElement.addEventListener(
    "change",
    (event) => {
      const roleSelect = event.target.closest(".role-select");
      if (roleSelect) {
        const [_, activityId, staffId] = roleSelect.id.split("--");
        window.pywebview.api.role_changed({
          activityId,
          staffId,
          roleId: roleSelect.value,
        });
      }
    },
    { signal: aborter.signal },
  );
}
function animateElementRemoval(tableElement, aborter) {
  tableElement.addEventListener(
    "animationend",
    (event) => {
      const activityWrapper = event.target.closest(".activity-wrapper");
      if (activityWrapper && activityWrapper.classList.contains("remove")) {
        activityWrapper.remove();
      }
    },
    { signal: aborter.signal },
  );
}
function doubleClickListener(tableElement, aborter) {
  tableElement.addEventListener(
    "dblclick",
    (event) => {
      const activityWrapper = event.target.closest(".activity-wrapper");
      if (activityWrapper) {
        const activityId = activityWrapper.dataset.activityId;
        window.pywebview.api.edit_activity({ activityId });
      }
    },
    { signal: aborter.signal },
  );
}

//create a web component for the table which will encapsulate the table and its functionality
class RotaTable extends HTMLElement {
  constructor() {
    super();
    this._cleanup = null;
    this._aborter = null;
  }

  connectedCallback() {
    this._aborter = new AbortController();
    const tableType = this.getAttribute("tabletype");
    watchDraggables(this, this._aborter, tableType);
    roleChangeListener(this, this._aborter);
    animateElementRemoval(this, this._aborter);
    doubleClickListener(this, this._aborter);
  }
  disconnectedCallback() {
    this._aborter?.abort();
    this._aborter = null;
  }
}
customElements.define("rota-table-wrapper", RotaTable);
