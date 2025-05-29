function setupTable() {
  const table = document.getElementById("rota-table");
  let draggedOverElement = null;
  let dragType = null;
  let dropTarget = null;
  let dragEffect = null;

  async function processFetch(response) {
    try {
      if (!response.ok) {
        throw new Error("Network response was not ok.");
      }
      const data = await response.text();

      console.log("Response:", data);

      Turbo.renderStreamMessage(data);
    } catch (error) {
      console.error("Error:", error);
    }
  }

  table.addEventListener("dragstart", function (event) {
    if (event.target.matches(".activity")) {
      event.dataTransfer.setData(
        "text/plain",
        JSON.stringify({
          activityId: event.target.dataset.activityId,
          from: event.target.closest("td").dataset,
        })
      );
      console.log(event.target.closest("td"));
      if (event.ctrlKey) {
        event.dataTransfer.effectAllowed = "copy";
        dragEffect = "copy";
      } else {
        event.dataTransfer.effectAllowed = "move";
        dragEffect = "move";
      }
      dragType = "activity";
    } else if (event.target.matches(".staff-allocation")) {
      event.dataTransfer.setData(
        "text/plain",
        JSON.stringify({
          staffId: event.target.dataset.staffId,
          from: event.target.closest(".activity").dataset,
        })
      );
      if (event.ctrlKey) {
        event.dataTransfer.effectAllowed = "copy";
        dragEffect = "copy";
      } else {
        event.dataTransfer.effectAllowed = "move";
        dragEffect = "move";
      }
      dragType = "staff";
    }
  });
  table.addEventListener("dragend", function (event) {
    dragType = null;

    if (dropTarget) {
      dropTarget.classList.remove("drag-over");
      dropTarget = null;
    }
  });
  table.addEventListener("dragenter", function (event) {
    const newDropTarget = event.target.closest(
      dragType == "activity" ? "td" : ".activity"
    );
    if (newDropTarget) {
      event.preventDefault(); // allow drop
    }

    if (newDropTarget !== dropTarget) {
      dropTarget?.classList.remove("drag-over");
    }
    newDropTarget?.classList?.add("drag-over");

    draggedOverElement = event.target;
    dropTarget = newDropTarget;
  });
  table.addEventListener("dragover", function (event) {
    if (dropTarget) {
      event.preventDefault(); // allow drop
    }
  });
  table.addEventListener("dragleave", function (event) {
    if (draggedOverElement === event.target) {
      draggedOverElement = null;
      dropTarget.classList.remove("drag-over");
      dropTarget = null;
    } // this only happens if the dragged element is not moved to another cell
  });
  table.addEventListener("drop", function (event) {
    event.preventDefault(); // prevent default action (open as link for some elements)
    if (dragType == "activity") {
      const data = JSON.parse(event.dataTransfer.getData("text/plain"));
      const targetCell = dropTarget.closest("td");
      if (targetCell.id !== data.from) {
        const payload = {
          location: "drag_activity",
          dragEffect: dragEffect,
          activityId: data.activityId,
          from_cell: data.from,
          to_cell: targetCell.dataset,
        };
        fetch("drag_activity", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }).then(processFetch);
        console.log("drop", { to: targetCell.dataset, ...data });
      }
    } else if (dragType == "staff") {
      const data = JSON.parse(event.dataTransfer.getData("text/plain"));
      const targetActivity = dropTarget.closest(".activity");
      const payload = {
        location: "drag_staff",
        dragEffect: dragEffect,
        staffId: data.staffId,
        from_activity: data.from.activityId,
        to_activity: targetActivity.dataset.activityId,
      };
      fetch("drag_staff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }).then(processFetch);
      dropTarget.classList.remove("drag-over");
      dropTarget = null;
    }
  });
  table.addEventListener("contextmenu", function (event) {
    const targetCell = event.target.closest("td");
    const linkParams = new URLSearchParams(targetCell?.dataset);

    if (!targetCell) {
      return; // If not a valid cell or no link, do nothing
    }
    event.preventDefault(); // prevent default context menu
    fetch(`/rota_grid/context_menu?${linkParams.toString()}`, {
      headers: { Accept: "text/vnd.turbo-stream.html" },
    }).then(processFetch);
  });
}
document.addEventListener("DOMContentLoaded", setupTable);
document.addEventListener("click", function (event) {
  if (
    !event.target.closest("#context-menu") &&
    document.querySelector("#context-menu:not(:empty)")
  ) {
    // If the click is outside the context menu, remove it
    event.preventDefault();
    document.querySelector("#context-menu").innerHTML = "";
  }
});
