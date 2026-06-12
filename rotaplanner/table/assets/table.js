function watchDraggables(tableElement) {
  let droptarget = null;
  let initialTarget = null;
  let maybedragging = false;
  let shiftKey = false;
  let altKey = false;
  let ctrlKey = false;
  let isdragging = false;
  let offsetX = 0;
  let offsetY = 0;
  const aborter = new AbortController();
  tableElement.addEventListener(
    "pointerdown",
    (event) => {
      if (event.target.closest("[data-draggable]")) {
        maybedragging = true;
        shiftKey = event.shiftKey;
        altKey = event.altKey;
        ctrlKey = event.ctrlKey;
        event.stopPropagation();
      }
    },
    { signal: aborter.signal },
  );
  tableElement.addEventListener(
    "pointermove",
    (event) => {
      const element = event.target.closest("[data-draggable]");
      const allowedTargetsSelector = element?.dataset.draggable;
      console.log(
        "Pointer move on",
        element,
        "maybedragging:",
        maybedragging,
        "isdragging:",
        isdragging,
      );
      if (!element) {
        return;
      }
      if (maybedragging && !isdragging) {
        element.dataset.dragging = "true";
        if (ctrlKey) {
          element.dataset.ctrldrag = "true";
        }
        initialTarget = element.closest(allowedTargetsSelector);
        element.dispatchEvent(
          new CustomEvent("begin-drag", {
            detail: {
              target: element,
              initialTarget: initialTarget,
              shiftKey,
              altKey,
              ctrlKey,
            },
            bubbles: true,
          }),
        );
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
            droptarget.dispatchEvent(
              new CustomEvent("drag-leave", {
                detail: { droptarget: droptarget, shiftKey, altKey, ctrlKey },
                bubbles: true,
              }),
            );
            delete droptarget.dataset.dragover;
          }
          droptarget = newdroptarget;
          if (droptarget) {
            droptarget.dispatchEvent(
              new CustomEvent("drag-enter", {
                detail: { droptarget: droptarget, shiftKey, altKey, ctrlKey },
                bubbles: true,
              }),
            );
            droptarget.dataset.dragover = "true";
          }
        }
        element.style.transform = `translate(${offsetX}px, ${offsetY}px)`;
        console.log("Droptarget:", droptarget, droptargets);
        element.dispatchEvent(
          new CustomEvent("dragging-over", {
            detail: { droptarget: droptarget, shiftKey, altKey, ctrlKey },
            bubbles: true,
          }),
        );
        if (droptarget) {
          element.dataset.canDrop = "true";
        } else {
          delete element.dataset.canDrop;
        }

        // Handle drag move logic here
      }
    },
    { signal: aborter.signal },
  );
  tableElement.addEventListener(
    "pointerup",
    (event) => {
      const element = event.target.closest("[data-draggable]");
      console.log("Pointer up on", element);
      if (!element) {
        return;
      }
      maybedragging = false;
      element.style.transform = "";
      if (isdragging) {
        isdragging = false;
        delete element.dataset.dragging;
        delete element.dataset.ctrldrag;
        delete element.dataset.canDrop;
        element.releasePointerCapture(event.pointerId);
        if (droptarget) {
          delete droptarget.dataset.dragover;
          droptarget.dispatchEvent(
            new CustomEvent("dropped-on", {
              detail: {
                droppedElement: element,
                shiftKey,
                altKey,
                ctrlKey,
                initialTarget,
              },
              bubbles: true,
            }),
          );
          window.pywry.emit("table:dropped", {
            droptarget: droptarget.id,
            shiftKey,
            altKey,
            ctrlKey,
            initialTarget: initialTarget ? initialTarget.id : null,
          });
          element.dispatchEvent(
            new CustomEvent("dropped", {
              detail: {
                droptarget: droptarget,
                shiftKey,
                altKey,
                ctrlKey,
                initialTarget: initialTarget ? initialTarget.id : null,
              },
              bubbles: true,
            }),
          );
        }
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
}

function roleChangeListener(tableElement) {
  tableElement.addEventListener("change", (event) => {
    const roleSelect = event.target.closest(".role-select");
    if (roleSelect) {
      const [_, activityId, staffId] = roleSelect.id.split("--");
      window.pywry.emit("table:role-changed", {
        activityId,
        staffId,
        roleId: roleSelect.value,
      });
    }
  });
}

function register() {
  const tableElement = document.getElementById("table");
  if (tableElement) {
    console.log("Watching draggables in table");
    watchDraggables(tableElement);
    roleChangeListener(tableElement);
  } else {
    console.warn("Table element not found, draggables will not work");
    window.setTimeout(register, 1000);
  }
}
window.setTimeout(register, 1000);
