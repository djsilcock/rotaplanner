// new_rotaplanner/ui/table/dragdrop.ts
function registerDraggable(element, allowedTargets, aborter) {
  let droptarget = null;
  let maybedragging = false;
  let isdragging = false;
  let offsetX = 0;
  let offsetY = 0;
  element.addEventListener(
    "pointerdown",
    (event) => {
      maybedragging = true;
      event.stopPropagation();
    },
    { signal: aborter }
  );
  element.addEventListener(
    "pointermove",
    (event) => {
      if (maybedragging && !isdragging) {
        element.dispatchEvent(
          new CustomEvent("begin-drag", {
            detail: { target: element, initialDropzone: element.closest(allowedTargets) },
            bubbles: true
          })
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
          event.clientY
        );
        droptarget = droptargets.find(
          (el) => el !== element && el.matches(allowedTargets || "")
        ) ?? null;
        element.style.transform = `translate(${offsetX}px, ${offsetY}px)`;
        element.dispatchEvent(
          new CustomEvent("dragging-over", {
            detail: { droptarget },
            bubbles: true
          })
        );
      }
    },
    { signal: aborter }
  );
  element.addEventListener(
    "pointerup",
    (event) => {
      maybedragging = false;
      element.style.transform = "";
      if (isdragging) {
        isdragging = false;
        element.releasePointerCapture(event.pointerId);
        if (droptarget) {
          droptarget.dispatchEvent(
            new CustomEvent("dropped-on", {
              detail: { droppedElement: element },
              bubbles: true
            })
          );
          element.dispatchEvent(
            new CustomEvent("dropped", {
              detail: { droptarget },
              bubbles: true
            })
          );
        }
      }
    },
    { signal: aborter }
  );
  element.addEventListener(
    "pointercancel",
    (event) => {
      if (isdragging) {
        element.dispatchEvent(
          new CustomEvent("drag-cancelled", {
            detail: { target: element },
            bubbles: true
          })
        );
      }
      isdragging = false;
      maybedragging = false;
      element.style.transform = "";
      element.releasePointerCapture(event.pointerId);
    },
    { signal: aborter }
  );
}
function dragdrop_default(datastar) {
  datastar.attribute({
    name: "draggable",
    requirement: {
      key: "denied",
      value: "must"
    },
    returnsValue: true,
    apply({ el, rx }) {
      const aborter = new AbortController();
      registerDraggable(el, rx(), aborter.signal);
      return () => aborter.abort();
    }
  });
}

// new_rotaplanner/ui/js.js
function setupDataStar(datastarInstance) {
  dragdrop_default(datastarInstance);
}
export {
  setupDataStar
};
//# sourceMappingURL=js.js.map
