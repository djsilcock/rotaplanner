function setupDropdown(uid) {
  // Element caching
  const container = document.getElementById(`container-${uid}`);
  const trigger = document.getElementById(`trigger-${uid}`);
  const panel = document.getElementById(`panel-${uid}`);
  const searchInput = document.getElementById(`search-${uid}`);
  const optionsList = document.getElementById(`options-${uid}`);
  const optionItems = optionsList.querySelectorAll(
    'li:not([id^="no-results-"])',
  );
  const noResults = document.getElementById(`no-results-${uid}`);
  const tagContainer = document.getElementById(`tags-${uid}`);
  const placeholder = document.getElementById(`placeholder-${uid}`);
  const chevronIcon = document.getElementById(`chevron-${uid}`);
  const nativeSelect = document.getElementById(`native-select-${uid}`);

  let isOpen = false;
  let selectedValues = new Set();

  Array.from(nativeSelect.options).forEach((opt) => {
    if (opt.selected) {
      selectedValues.add(opt.value);
    }
  });

  function toggleDropdown(forceState = null) {
    isOpen = forceState !== null ? forceState : !isOpen;
    if (isOpen) {
      panel.classList.add("open");
      chevronIcon.classList.add("rotate-180");
      setTimeout(() => searchInput.focus(), 50);
    } else {
      panel.classList.remove("open");
      chevronIcon.classList.remove("rotate-180");
      searchInput.value = "";
      filterOptions("");
    }
  }

  function syncNativeSelect() {
    // Reset all native options
    Array.from(nativeSelect.options).forEach((opt) => {
      opt.selected = selectedValues.has(opt.value);
    });

    // Fire a change event on the native element to support standard handlers
    const changeEvent = new Event("change", { bubbles: true });
    nativeSelect.dispatchEvent(changeEvent);
  }

  function renderTags() {
    tagContainer.innerHTML = "";

    if (selectedValues.size === 0) {
      placeholder.classList.remove("ms-hidden");
    } else {
      placeholder.classList.add("ms-hidden");
    }

    selectedValues.forEach((val) => {
      const item = Array.from(optionItems).find(
        (i) => i.getAttribute("data-value") === val,
      );
      if (!item) return;
      const label = item.getAttribute("data-name");

      const pill = document.createElement("div");
      pill.className = "ms-tag";

      const labelSpan = document.createElement("span");
      labelSpan.textContent = label;

      const closeBtn = document.createElement("button");
      closeBtn.type = "button";
      closeBtn.className = "ms-tag-remove";
      closeBtn.innerHTML = `
                                <svg fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"></path>
                                </svg>
                            `;
      closeBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        toggleItem(val);
      });

      pill.appendChild(labelSpan);
      pill.appendChild(closeBtn);
      tagContainer.appendChild(pill);
    });
  }

  function toggleItem(val) {
    const item = Array.from(optionItems).find(
      (i) => i.getAttribute("data-value") === val,
    );
    if (!item) return;

    const checkbox = item.querySelector(".ms-checkbox-indicator");
    const svg = checkbox.querySelector(".ms-check-mark");

    if (selectedValues.has(val)) {
      selectedValues.delete(val);
      item.classList.remove("selected");
      svg.classList.add("hidden");
    } else {
      selectedValues.add(val);
      item.classList.add("selected");
      svg.classList.remove("hidden");
    }

    syncNativeSelect();
    renderTags();
  }

  function filterOptions(query) {
    const cleanQuery = query.toLowerCase().trim();
    let matches = 0;

    optionItems.forEach((item) => {
      const name = item.getAttribute("data-name").toLowerCase();
      if (name.includes(cleanQuery)) {
        item.classList.remove("ms-hidden");
        matches++;
      } else {
        item.classList.add("ms-hidden");
      }
    });

    if (matches === 0) {
      noResults.classList.remove("ms-hidden");
    } else {
      noResults.classList.add("ms-hidden");
    }
  }

  // Setup localized click listeners
  trigger.addEventListener("click", () => toggleDropdown());

  searchInput.addEventListener("input", (e) => {
    filterOptions(e.target.value);
  });

  searchInput.addEventListener("keydown", (e) => {
    if (e.key === " ") e.stopPropagation();
  });

  optionItems.forEach((item) => {
    item.addEventListener("click", () => {
      const val = item.getAttribute("data-value");
      toggleItem(val);
      searchInput.focus();
    });
  });

  // Global body listener to close dropdown, verified via container scope
  document.addEventListener("click", (e) => {
    if (!container.contains(e.target)) {
      toggleDropdown(false);
    }
  });
}
