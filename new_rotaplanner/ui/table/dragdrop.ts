function registerDraggable(
  element: HTMLElement,
  allowedTargets: string,
  aborter?: AbortSignal
) {
  let droptarget: HTMLElement | null = null;
  let maybedragging: boolean = false;
  let isdragging: boolean = false;
  let offsetX: number = 0;
  let offsetY: number = 0;
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
            detail: { target: element,initialDropzone:element.closest(allowedTargets) },
            bubbles: true,
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
        ) as HTMLElement[];

        droptarget =
          droptargets.find(
            (el) => el !== element && el.matches(allowedTargets || "")
          ) ?? null;

        element.style.transform = `translate(${offsetX}px, ${offsetY}px)`;

        element.dispatchEvent(
          new CustomEvent("dragging-over", {
            detail: { droptarget: droptarget },
            bubbles: true,
          })
        );

        // Handle drag move logic here
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
              bubbles: true,
            })
          );
          element.dispatchEvent(
            new CustomEvent("dropped", {
              detail: { droptarget: droptarget },
              bubbles: true,
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
            bubbles: true,
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

export default function (datastar) {
  datastar.attribute({
    name: "draggable",
    requirement: {
      key: "denied",
      value: "must",
    },
    returnsValue: true,
    apply({ el, rx }: { el: HTMLElement; rx: () => string }) {
      const aborter = new AbortController();
      registerDraggable(el, rx(), aborter.signal);

      return () => aborter.abort();
    },
  });
}
