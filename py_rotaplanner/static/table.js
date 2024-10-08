up.compiler("#rota-table", (table) => {
  let draglimit = "";
  let multiSelectMode;
  let draggedElements = [];
  let dragIsValid = true;
  function getRowAndColumn(
    element,
    { row: zeroRow = 0, column: zeroColumn = 0 } = {}
  ) {
    const containingRow = element.closest("tr");
    const containingCell = element.closest("td");
    const rowCells = Array.from(
      containingRow.querySelectorAll(
        "td.activitycell,td.unallocated-activities"
      )
    );
    const columnIndex = rowCells.indexOf(containingCell);
    const rowIndex = Array.from(
      containingRow.closest("tbody").querySelectorAll("tr")
    ).indexOf(containingRow);
    console.log({ element, rowIndex, zeroRow, columnIndex, zeroColumn });
    return { row: rowIndex - zeroRow, column: columnIndex - zeroColumn };
  }
  function getCells(entries) {
    const result = [];
    const table = document.getElementById("rota-table-content");
    const rows = Array.from(table.querySelectorAll("tr"));
    for (let entry of entries) {
      const targetRow = rows[entry.row];
      targetCell = Array.from(
        targetRow.querySelectorAll("td.activitycell,td.unallocated-activities")
      )[entry.column];
      result.push({ ...entry, cell: targetCell });
    }
    return result;
  }
  function highlightCells(entries) {
    for (let entry of getCells(entries)) {
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
    //is this multi-select?
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
        initialstaff: el.dataset.staff,
        ...getRowAndColumn(el, getRowAndColumn(e.target)),
      });
    }
    draglimit = "td.activitycell,td.unallocated-activities";

    const payload = JSON.stringify({
      initialstaff: e.target.dataset.staff,
      activities: Array.from(selectedElements, (el) => el.dataset.activityid),
    });
    e.dataTransfer.setData("text/plain", payload);
    e.dataTransfer.setDragImage(document.getElementById("empty"), 0, 0);
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
    const target = e.target.closest("td");
    if (!target) return;
    console.log("dragover", getRowAndColumn(target));
    const { row, column } = getRowAndColumn(target);
    document
      .querySelectorAll("td.activitycell")
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
        .querySelectorAll("td.activitycell")
        .forEach((el) =>
          el.classList.remove("dragover-valid", "dragover-invalid")
        );
    }
  });
  table.addEventListener("dragleave", (e) => {
    e.target.classList.remove("dragover-valid", "dragover-invalid");
  });

  table.addEventListener("drop", (e) => {
    console.log("drop", e.target);
    const { initialstaff, activities } = JSON.parse(
      e.dataTransfer.getData("text/plain")
    );

    const droptarget = e.target.closest("td");
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
      entry.newstaff = entry.cell.dataset.staff;
      entry.newdate = entry.cell.dataset.date;
      console.log(entry);
    }
    up.render(`#${droptarget.id}:maybe`, {
      url: "/api/activities/reallocate",
      method: "POST",
      contentType: "application/json",
      payload: JSON.stringify({ entries: dropEntries }),
      failLayer: "new drawer",
      failTarget: ".error-popup",
    }).finally(() => {
      draglimit = "";
    });
  });
});
