/*up.on("up:deferred:load", "#entryzone", (ev, el) => {
  const firstpos = document.querySelector(".column-header");
  ev.renderOptions.onRendered = (ev) => {
    console.log(firstpos, firstpos.offsetLeft);
    console.log(document.querySelector("#rota-scrollable").scrollLeft);
    document.querySelector("#rota-scrollable").scrollLeft = firstpos.offsetLeft;
  };
});*/
import "./table.css";
up.compiler(
  "#rota-scrollable",
  (scrollContainer, { today, first, last, yAxis }) => {
    const SEGMENT_WIDTH = 10;
    const scrollContent = document.getElementById("rota-grid");
    let todayCell;
    let itemCount = 0;
    let timeout = true;

    // Function to generate a new item
    const createItem = (id) => {
      const wrapper = document.createElement("div");
      wrapper.classList.add("rota-segment-wrapper");
      const item = document.createElement("div");
      wrapper.appendChild(item);
      item.classList.add("rota-segment");

      item.textContent = "...";
      item.dataset.page = id;
      wrapper.dataset.page = id;
      item.id = `rota-segment-${id}`;
      item.setAttribute("up-defer", "reveal");
      item.setAttribute(
        "up-href",
        `/activities/rota_segment?y_axis=${yAxis}&start_date=${id}`
      );

      return wrapper;
    };

    // Function to append items to the right
    const appendItem = () => {
      const lastChild = scrollContent.lastChild;
      const thisId =
        Number(lastChild?.dataset.page || first - SEGMENT_WIDTH) +
        SEGMENT_WIDTH;

      const newItem = createItem(thisId);
      console.log(newItem);
      if (today >= thisId && today < thisId + SEGMENT_WIDTH) {
        todayCell = newItem;
        console.log("yep");
      }
      scrollContent.appendChild(newItem);
      return [newItem, thisId];
    };

    // Function to prepend items to the left

    // Prepopulate the scroll content with some items
    console.log({ first, last, today });
    for (let i = first; i <= last; i = appendItem()[1]) {}
    if (todayCell) {
      scrollContainer.scrollLeft = todayCell.offsetLeft;
    }
    document.querySelectorAll(".rota-segment").forEach((el) => up.hello(el));
    // Handle the scroll event

    const prependedObserver = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (!e.isIntersecting) {
          if (e.target == scrollContent.firstChild) {
            scrollContainer.scrollLeft -= e.target.offsetWidth;
            prependedObserver.unobserve(e.target);
            e.target.remove();
          }
        }
      });
    });
    const prependObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            const firstChild = scrollContent.firstChild;
            const firstId = Number(firstChild.dataset.page);

            const newItem = createItem(firstId - SEGMENT_WIDTH);
            console.log({ firstId, firstChild });
            if (firstId < first) newItem.classList.add("prepend");
            scrollContent.insertBefore(newItem, scrollContent.firstChild);
            scrollContainer.scrollLeft = firstChild.offsetLeft;
            console.log({ newItem, firstChild });
            setTimeout(() => up.hello(newItem), 500);
          }
        });
      },
      { root: scrollContainer }
    );
    prependObserver.observe(document.querySelector("#grid-begin"));
    const appendObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            lastitem = scrollContent.lastChild;
            const item = appendItem()[0];
            setTimeout(() => up.hello(item), 500);
          }
        });
      },
      { root: scrollContainer }
    );
    appendObserver.observe(document.querySelector("#grid-end"));
  }
);

up.compiler("#rota-table", (table) => {
  let draglimit = "";
  let dragmode = "";

  let multiSelectMode;
  let draggedElements = [];
  let dragIsValid = true;
  function getRowAndColumn(
    element,
    { row: zeroRow = 0, column: zeroColumn = 0 } = {}
  ) {
    const columns = Array.from(
      document.querySelectorAll(".column-header"),
      (e) => e.dataset.date
    );
    const rows = Array.from(
      document.querySelectorAll(".row-header"),
      (e) => e.dataset.yaxis
    );
    const containingCell = element.closest(
      ".activitycell,.unallocated-activities"
    );
    console.log({ rows, columns, containingCell });
    const columnIndex = columns.indexOf(containingCell.dataset.date);
    const rowIndex = rows.indexOf(containingCell.dataset.yaxis);
    console.log({ element, rowIndex, zeroRow, columnIndex, zeroColumn });
    return { row: rowIndex - zeroRow, column: columnIndex - zeroColumn };
  }
  function getCells(entries) {
    const result = [];
    const columns = Array.from(
      document.querySelectorAll(".column-header"),
      (e) => e.dataset.date
    );
    const rows = Array.from(
      document.querySelectorAll(".row-header"),
      (e) => e.dataset.yaxis
    );
    console.log(rows);
    for (let entry of entries) {
      targetCell = document.querySelector(
        `[data-date="${columns[entry.column]}"]:is([data-yaxis="${
          rows[entry.row]
        }"])`
      );
      result.push({ ...entry, cell: targetCell });
    }
    return result;
  }
  function highlightCells(entries) {
    for (let entry of getCells(entries)) {
      entry.cell.classList.add("dragover-valid");
      return;
      const selector = `.unallocated-activities[data-date="${entry.cell.dataset.date}"] .activity[data-activityid="${entry.activityid}"]`;
      console.log(entry, selector, document.querySelectorAll(selector));
      if (document.querySelectorAll(selector).length > 0) {
        entry.cell.classList.add("dragover-valid");
      } else {
        entry.cell.classList.add("dragover-invalid");
      }
    }
  }
  table.addEventListener("dragstart", (e) => {
    const selectedElements = new Set([e.target]);
    let payload;
    //is this multi-select?
    if (e.target.matches(".assignment")) {
      console.log("dragging assignment");
      dragmode = "assignment";
      draglimit = ".activity,.unallocated-activities";
      payload = JSON.stringify({
        staff: e.target.dataset.staff,
        initialactivity: e.target.closest(".activity").dataset.activityid,
      });
      e.dataTransfer.setData("text/plain", payload);
      //e.dataTransfer.setDragImage(document.getElementById("empty"), 0, 0);
    } else if (e.target.matches(".activity")) {
      console.log("dragging activity");
      dragmode = "activity";
      document.querySelectorAll(".activity.selected").forEach((el) => {
        selectedElements.add(el);
      });

      multiSelectMode = selectedElements.size > 1;
      //all must be the same name
      draggedElements = [];
      for (let el of selectedElements) {
        console.log(getRowAndColumn(el, getRowAndColumn(e.target)));
        draggedElements.push({
          activityid: el.dataset.activityid,
          initialdate: el.dataset.activitydate,
          initialposition: el.dataset.yaxis,
          ...getRowAndColumn(el, getRowAndColumn(e.target)),
        });
      }
      draglimit = ".activitycell,.unallocated-activities";

      payload = JSON.stringify({
        initialposition: e.target.dataset.yaxis,
        activities: Array.from(selectedElements, (el) => el.dataset.activityid),
      });
      e.dataTransfer.setData("text/plain", payload);
      //e.dataTransfer.setDragImage(document.getElementById("empty"), 0, 0);
    }
  });
  table.addEventListener("dragend", (e) => {
    document.querySelectorAll(".activitycell").forEach((cell) => {
      cell.classList.remove("dragover-valid", "dragover-invalid");
      draglimit = "";
    });
  });
  table.addEventListener("click", (e) => {
    const selectedActivity = e.target.closest(".activity");

    if (!e.ctrlKey) {
      document.querySelectorAll(".activity").forEach((act) => {
        act.classList.remove("selected");
      });
    }
    if (selectedActivity == null) return;
    selectedActivity.classList.toggle("selected");
  });
  table.addEventListener("dragover", (e) => {
    if (e.target.closest(draglimit) && dragIsValid) e.preventDefault();
  });
  table.addEventListener("dragenter", (e) => {
    if (dragmode == "assignment") {
      const target = e.target.closest(".activity");
      console.log(e.target, target);
      if (!target) return;
      document
        .querySelectorAll(".activity")
        .forEach((el) => el.classList.remove("dragover"));
      target.classList.add("dragover");
    }

    if (dragmode == "activity") {
      const target = e.target.closest(".activitycell");
      if (!target) return;
      console.log("dragover", getRowAndColumn(target));
      const { row, column } = getRowAndColumn(target);
      document
        .querySelectorAll(".activitycell")
        .forEach((el) =>
          el.classList.remove("dragover-valid", "dragover-invalid")
        );

      try {
        highlightCells(
          draggedElements.map((entry) => ({
            ...entry,
            row: row + entry.row,
            column: column + entry.column,
          }))
        );
        dragIsValid = true;
      } catch (e) {
        console.warn(e);
        dragIsValid = false;
        document
          .querySelectorAll(".activitycell")
          .forEach((el) =>
            el.classList.remove("dragover-valid", "dragover-invalid")
          );
      }
    }
  });
  table.addEventListener("dragleave", (e) => {
    e.target.classList.remove("dragover-valid", "dragover-invalid", "dragover");
  });

  table.addEventListener("drop", (e) => {
    console.log("drop", e.target);
    if (dragmode == "activity") {
      const droptarget = e.target.closest(
        ".activitycell,.unallocated-activities"
      );
      if (!droptarget) return;
      console.log("drop", getRowAndColumn(droptarget));
      const { row, column } = getRowAndColumn(droptarget);
      let dropEntries;
      console.log(draggedElements);
      try {
        dropEntries = getCells(
          draggedElements.map((entry) => ({
            ...entry,
            row: row + entry.row,
            column: column + entry.column,
          }))
        );
      } catch {
        dragIsValid = false;
      }
      for (let entry of dropEntries) {
        entry.newposition = entry.cell.dataset.yaxis;
        entry.newdate = entry.cell.dataset.date;
        console.log(entry);
      }
      const formdata = new FormData();
      dropEntries.forEach((entry, i) => {
        ["activityid", "initialposition", "newposition", "newdate"].forEach(
          (v) => {
            if (entry[v]) formdata.append(`entries-${i}-${v}`, entry[v]);
          }
        );
      });

      up.render(`#${droptarget.id}:maybe`, {
        url: "/activities/reallocate_activity",
        method: "POST",
        headers: {
          "X-CSRFToken": document.getElementById("rota-table").dataset.csrf,
        },
        payload: formdata,
        failLayer: "new drawer",
        failTarget: ".error-popup",
      }).finally(() => {
        draglimit = "";
      });
    }
    if (dragmode == "assignment") {
      const { staff, initialactivity } = JSON.parse(
        e.dataTransfer.getData("text/plain")
      );

      const droptarget = e.target.closest(".activity");
      if (!droptarget) return;
      console.log({ droptarget });
      const newactivity = droptarget.dataset.activityid;
      const formdata = new FormData();
      formdata.append("staff", staff);
      formdata.append("initialactivity", initialactivity);
      formdata.append("newactivity", newactivity);

      up.render(`#${droptarget.id}:maybe`, {
        url: "/activities/reallocate_staff",
        method: "POST",
        headers: {
          "X-CSRFToken": document.getElementById("rota-table").dataset.csrf,
        },
        payload: formdata,
        failLayer: "new drawer",
        failTarget: ".error-popup",
      }).finally(() => {
        draglimit = "";
      });
    }
  });
});
