document.addEventListener("DOMContentLoaded", function () {
  $(".ui.sidebar").sidebar("attach events", "#menubutton");
});
document.addEventListener("turbo:before-fetch-request", function (event) {
  console.log(event);
});
document.addEventListener("turbo:frame-load", function (event) {
  console.log(event);
  if (event.target.id === "main") {
    // If the main frame is missing, reload the page
    window.location.reload();
  }
  if (event.target.id === "dialog") {
    // If the main frame is missing, reload the page
    $(".ui.modal").modal("show", { detachable: false });
  }
  $(".ui.dropdown").dropdown();
  $(".ui.accordion").accordion();
  console.warn("Frame loaded: " + event.target.id);
});
