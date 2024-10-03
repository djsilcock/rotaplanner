function ordinal(index) {
  index = index % 100;
  if (Math.floor(index / 10) == 1) return `${index}th`;
  if (index % 10 == 1) return `${index}st`;
  if (index % 10 == 2) return `${index}nd`;
  if (index % 10 == 3) return `${index}rd`;
  return `${index}th`;
}
const weekdays = [
  "Sunday",
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];
up.compiler(".rule-definition", (element) => {
  function onChange() {
    const description = element.querySelector(".description");
    const ruleType = element.querySelector(".rule-type").value;
    const date = new Date(element.querySelector('input[type="date"]').value);
    switch (ruleType) {
      case "group":
        description.innerText = element.querySelector(
          ".group-type option:checked"
        ).label;
        break;
      case "daily":
        description.innerText = `${
          element.querySelector(".day-interval option:checked").label
        } starting ${date.toDateString()}`;
        break;
      case "weekly":
        description.innerText = `${weekdays[date.getDay()]} of ${
          element.querySelector(".week-interval option:checked").label
        } starting ${date.toDateString()}`;
        break;
      case "day-in-month":
        description.innerText = `${ordinal(date.getDate())} of ${
          element.querySelector(".month-interval option:checked").label
        } starting ${date.toDateString()}`;
        break;
      case "week-in-month":
        description.innerText = `The ${ordinal(
          Math.floor(date.getDate() / 7) + 1
        )} ${weekdays[date.getDay()]} of ${
          element.querySelector(".month-interval option:checked").label
        } starting ${date.toDateString()}`;
        break;
      default:
        description.innerText = "";
    }
  }
  onChange();
  element.addEventListener("change", onChange);
});
