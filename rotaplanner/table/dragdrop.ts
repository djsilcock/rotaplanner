import { Accessor, onCleanup } from "solid-js";

export function registerDraggable(
  element: HTMLElement,
  allowedTargets: Accessor<string>,
) {
  let droptarget: HTMLElement | null = null;
  let initialTarget: HTMLElement | null = null;
  let maybedragging: boolean = false;
  let shiftKey: boolean = false;
  let altKey: boolean = false;
  let ctrlKey: boolean = false;
  let isdragging: boolean = false;
  let offsetX: number = 0;
  let offsetY: number = 0;
  const aborter = new AbortController();
  onCleanup(() => {
    aborter.abort();
  });
  element.addEventListener(
    "pointerdown",
    (event) => {
      maybedragging = true;
      shiftKey = event.shiftKey;
      altKey = event.altKey;
      ctrlKey = event.ctrlKey;
      event.stopPropagation();
    },
    { signal: aborter.signal },
  );
  element.addEventListener(
    "pointermove",
    (event) => {
      if (maybedragging && !isdragging) {
        element.dataset.dragging = "true";
        if (ctrlKey) {
          element.dataset.ctrldrag = "true";
        }
        initialTarget = element.closest(allowedTargets());
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
        ) as HTMLElement[];

        let newdroptarget =
          droptargets.find(
            (el) => el !== element && el.matches(allowedTargets()),
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
  element.addEventListener(
    "pointerup",
    (event) => {
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
          element.dispatchEvent(
            new CustomEvent("dropped", {
              detail: {
                droptarget: droptarget,
                shiftKey,
                altKey,
                ctrlKey,
                initialTarget,
              },
              bubbles: true,
            }),
          );
        }
      }
    },
    { signal: aborter.signal },
  );
  element.addEventListener(
    "pointercancel",
    (event) => {
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
