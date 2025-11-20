import { createSignal, createSelector, createEffect } from "solid-js";

export default class DragDrop {
  droptargets: WeakMap<HTMLElement, any> = new WeakMap();
  draggables: WeakMap<HTMLElement, any> = new WeakMap();
  #maybeCurrentDrag: HTMLElement | null = null;
  #currentDrag;
  #currentDrop;

  constructor() {
    this.#currentDrag = createSignal<HTMLElement | null>(null);
    this.#currentDrop = createSignal<HTMLElement | null>(null);
  }
  get currentDrag() {
    return this.#currentDrag[0]();
  }
  get currentDroptarget() {
    return this.#currentDrop[0]();
  }
  set currentDrag(value: HTMLElement | null) {
    this.#currentDrag[1](value);
  }
  set currentDroptarget(value: HTMLElement | null) {
    this.#currentDrop[1](value);
  }
  registerDroptarget(element: HTMLElement, options: any) {
    const defaultOptions = {
      canDrop(draggedElementInfo: any) {
        return true;
      },
    };
    options = { ...defaultOptions, ...options };
    this.droptargets.set(element, options);
  }
  registerDraggable(element: HTMLElement, options: () => any) {
    const defaultOptions = {
      data: null,
      setIsCurrentDrag: (isCurrent: boolean) => {},
      onDragStart: (event: PointerEvent) => {
        element.dataset.dndIsDragging = "true";
      },
      onDragEnd: (event: PointerEvent) => {
        element.style.transform = "";
        delete element.dataset.dndCanDrop;
        delete element.dataset.dndIsDragging;
      },
      onDragMove: (event: {
        event: PointerEvent;
        offsetX: number;
        offsetY: number;
        droptarget: HTMLElement | null;
      }) => {
        element.style.transform = `translate(${event.offsetX}px, ${event.offsetY}px)`;
        if (event.droptarget) {
          element.dataset.dndCanDrop = "true";
        } else {
          element.dataset.dndCanDrop = "false";
        }
      },
    };
    const _options = { ...defaultOptions, ...options() };
    this.draggables.set(element, _options.data);

    let offsetX: number;
    let offsetY: number;
    let clientX: number;
    let clientY: number;
    element.addEventListener("pointerdown", (event) => {
      this.#maybeCurrentDrag = element;
    });
    element.addEventListener("pointerup", (event) => {
      this.#maybeCurrentDrag = null;
      if (this.currentDrag === element) {
        this.currentDrag = null;

        _options.setIsCurrentDrag(false);
        element.releasePointerCapture(event.pointerId);
        _options.onDragEnd(event);
        if (this.currentDroptarget) {
          this.droptargets
            .get(this.currentDroptarget)
            .onDrop?.({ draggedElementInfo: _options.data });
        }
      }
    });
    element.addEventListener("pointercancel", (event) => {
      if (this.currentDrag === element) {
        this.currentDrag = null;
        _options.setIsCurrentDrag(false);
        element.releasePointerCapture(event.pointerId);
        _options.onDragEnd(event);
      }
    });
    element.addEventListener("pointermove", (event) => {
      if (this.#maybeCurrentDrag == element && this.currentDrag == null) {
        this.currentDrag = element;
        _options.setIsCurrentDrag(true);
        offsetX = 0;
        offsetY = 0;

        _options.onDragStart(event);
        element.setPointerCapture(event.pointerId);
      }
      if (this.currentDrag === element) {
        offsetX += event.movementX;
        offsetY += event.movementY;
        const droptargets = document.elementsFromPoint(
          event.clientX,
          event.clientY
        ) as HTMLElement[];

        const droptarget =
          droptargets.find(
            (el) =>
              this.droptargets.has(el) &&
              this.droptargets.get(el).canDrop({
                draggedElementInfo: _options.data,
              })
          ) || null;
        _options.onDragMove({
          event,
          offsetX,
          offsetY,
          droptarget,
        });
        this.currentDroptarget = droptarget;
        if (droptarget !== this.currentDroptarget) {
          if (this.currentDroptarget) {
            this.droptargets.get(this.currentDroptarget).onDragLeave?.({
              draggedElementInfo: _options.data,
            });
          }
          if (droptarget) {
            this.droptargets.get(droptarget).onDragEnter?.({
              draggedElementInfo: _options.data,
            });
          }
          this.currentDroptarget = droptarget;
        }

        // Handle drag move logic here
      }
    });
  }
}
