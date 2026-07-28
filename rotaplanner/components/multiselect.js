class SearchableMultiSelect extends HTMLElement {
  // Allows the Web Component to integrate naturally into native <form> and FormData
  static formAssociated = true;

  constructor() {
    super();
    this.internals = this.attachInternals();
    this.attachShadow({ mode: "open" });

    this.selectedValues = new Set();
    this.isOpen = false;
    this.optionsData = [];
  }

  connectedCallback() {
    // Extract initial configuration properties/attributes
    this.name = this.getAttribute("name") || "multiselect";
    this.labelText = this.getAttribute("label") || "";
    this.placeholder = this.getAttribute("placeholder") || "Select options...";

    // Parse child <option> tags as primary data sources
    this.optionsData = Array.from(this.querySelectorAll("option")).map(
      (opt) => {
        let pill = opt.querySelector("span.pill");
        if (pill) {
          pill.remove(); // Remove pill from DOM to avoid duplication in the shadow DOM
        }
        return {
          value: opt.value,
          label: opt.textContent.trim(),
          pill: pill ? pill.textContent.trim() : opt.textContent.trim(),
          selected: opt.hasAttribute("selected"),
        };
      },
    );

    // Store initially selected keys
    this.optionsData.forEach((opt) => {
      if (opt.selected) this.selectedValues.add(opt.value);
    });

    this.renderShadowDOM();
    this.setupEventListeners();
    this.syncFormValue();
    this.renderTags();
  }

  renderShadowDOM() {
    const styleBlock = `
            <style>
                :host {
                    display: block;
                    width: 100%;
                    font-family: system-ui, -apple-system, sans-serif;
                    text-align: left;
                }
                .ms-container {
                    position: relative;
                    width: 100%;
                }
                .ms-label {
                    display: block;
                    font-size: 0.875rem;
                    font-weight: 600;
                    color: #334155;
                    margin-bottom: 0.5rem;
                }
                .ms-trigger {
                    width: 100%;
                    min-height: 46px;
                    padding: 0.375rem 0.75rem;
                    background-color: #ffffff;
                    border: 1px solid #cbd5e1;
                    border-radius: 0.75rem;
                    cursor: pointer;
                    display: flex;
                    flex-wrap: wrap;
                    align-items: center;
                    gap: 0.375rem;
                    box-sizing: border-box;
                    transition: border-color 0.2s, box-shadow 0.2s;
                }
                .ms-trigger:focus-within {
                    border-color: #4f46e5;
                    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.15);
                }
                .ms-placeholder {
                    color: #94a3b8;
                    font-size: 0.875rem;
                    user-select: none;
                    padding: 0.25rem 0;
                }
                .ms-tags {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 0.375rem;
                }
                .ms-tag {
                    display: flex;
                    align-items: center;
                    gap: 0.25rem;
                    background-color: #e0e7ff;
                    color: #4338ca;
                    font-size: 0.75rem;
                    font-weight: 600;
                    padding: 0.25rem 0.5rem;
                    border-radius: 0.5rem;
                    border: 1px solid rgba(79, 70, 229, 0.2);
                }
                .ms-tag-remove {
                    background: transparent;
                    border: none;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    color: #4338ca;
                    opacity: 0.7;
                    padding: 0;
                }
                .ms-tag-remove:hover {
                    opacity: 1;
                }
                .ms-tag-remove svg {
                    width: 0.875rem;
                    height: 0.875rem;
                }
                .ms-chevron-wrapper {
                    margin-left: auto;
                    padding-left: 0.5rem;
                    color: #94a3b8;
                    display: flex;
                    align-items: center;
                }
                .ms-chevron-icon {
                    width: 1.25rem;
                    height: 1.25rem;
                    transition: transform 0.2s;
                }
                .ms-chevron-icon.rotate {
                    transform: rotate(180deg);
                }
                .ms-panel {
                    position: absolute;
                    left: 0;
                    right: 0;
                    margin-top: 0.5rem;
                    background-color: #ffffff;
                    border: 1px solid #e2e8f0;
                    border-radius: 0.75rem;
                    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
                    z-index: 100;
                    overflow: hidden;
                    transform: scale(0.95);
                    opacity: 0;
                    pointer-events: none;
                    transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.15s ease-out;
                    transform-origin: top;
                    box-sizing: border-box;
                }
                .ms-panel.open {
                    transform: scale(1);
                    opacity: 1;
                    pointer-events: auto;
                }
                .ms-search-container {
                    padding: 0.75rem;
                    border-bottom: 1px solid #f1f5f9;
                    background-color: #f8fafc;
                }
                .ms-search-wrapper {
                    position: relative;
                    width: 100%;
                }
                .ms-search-icon-wrapper {
                    position: absolute;
                    top: 0;
                    bottom: 0;
                    left: 0;
                    padding-left: 0.75rem;
                    display: flex;
                    align-items: center;
                    pointer-events: none;
                    color: #94a3b8;
                }
                .ms-search-icon {
                    width: 1rem;
                    height: 1rem;
                }
                .ms-search-input {
                    width: 100%;
                    padding: 0.5rem 1rem 0.5rem 2.25rem;
                    font-size: 0.875rem;
                    background-color: #ffffff;
                    border: 1px solid #e2e8f0;
                    border-radius: 0.5rem;
                    outline: none;
                    color: #0f172a;
                    box-sizing: border-box;
                }
                .ms-search-input:focus {
                    border-color: #4f46e5;
                }
                .ms-options {
                    max-height: 200px;
                    overflow-y: auto;
                    padding: 0.25rem 0;
                    list-style: none;
                    margin: 0;
                }
                .ms-options::-webkit-scrollbar {
                    width: 5px;
                }
                .ms-options::-webkit-scrollbar-track {
                    background: #f1f1f1;
                }
                .ms-options::-webkit-scrollbar-thumb {
                    background: #cbd5e1;
                    border-radius: 4px;
                }
                .ms-option {
                    display: flex;
                    align-items: center;
                    padding: 0.625rem 1rem;
                    font-size: 0.875rem;
                    cursor: pointer;
                    user-select: none;
                    color: #334155;
                    transition: background-color 0.1s, color 0.1s;
                }
                .ms-option:hover {
                    background-color: #f8fafc;
                }
                .ms-option.selected {
                    background-color: rgba(79, 70, 229, 0.04);
                    color: #4338ca;
                }
                .ms-checkbox-indicator {
                    margin-right: 0.75rem;
                    width: 1.25rem;
                    height: 1.25rem;
                    border: 1px solid #cbd5e1;
                    border-radius: 0.375rem;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #cbd5e1;
                    transition: background-color 0.15s, border-color 0.15s;
                    background-color: #ffffff;
                    box-sizing: border-box;
                }
                .ms-option.selected .ms-checkbox-indicator {
                    background-color: #4f46e5;
                    border-color: #4f46e5;
                }
                .ms-check-mark {
                    width: 0.875rem;
                    height: 0.875rem;
                    color: #ffffff;
                    display: none;
                }
                .ms-option.selected .ms-check-mark {
                    display: block;
                }
                .ms-no-results {
                    padding: 1.25rem;
                    font-size: 0.875rem;
                    color: #64748b;
                    text-align: center;
                    font-style: italic;
                }
                .hidden {
                    display: none !important;
                }
            </style>
        `;

    // Generate Options HTML markup
    const optionsMarkup = this.optionsData
      .map((opt) => {
        const isSelected = this.selectedValues.has(opt.value);
        return `<li class="ms-option ${isSelected ? "selected" : ""}" data-value="${opt.value}" data-name="${opt.label}">
                    <span class="ms-checkbox-indicator">
                        <svg class="ms-check-mark" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5"></path>
                        </svg>
                    </span>
                    <span class="ms-option-label">${opt.label}</span>
                </li>
                `;
      })
      .join("");

    this.shadowRoot.innerHTML = `
                        ${styleBlock}
                        <div class="ms-container">
                            ${this.labelText ? `<label class="ms-label">${this.labelText}</label>` : ""}
                            
                            <div class="ms-trigger" id="trigger" tabindex="0">
                                <span class="ms-placeholder" id="placeholder">${this.placeholder}</span>
                                <div class="ms-tags" id="tags-container"></div>
                                <div class="ms-chevron-wrapper">
                                    <svg class="ms-chevron-icon" id="chevron" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7"></path>
                                    </svg>
                                </div>
                            </div>

                            <div class="ms-panel" id="panel">
                                <div class="ms-search-container">
                                    <div class="ms-search-wrapper">
                                        <div class="ms-search-icon-wrapper">
                                            <svg class="ms-search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                                            </svg>
                                        </div>
                                        <input type="text" id="search-field" placeholder="Type to search..." class="ms-search-input" />
                                    </div>
                                </div>
                                <ul class="ms-options" id="options-list">
                                    ${optionsMarkup}
                                    <li class="ms-no-results hidden" id="no-results">No matches found</li>
                                </ul>
                            </div>
                        </div>
                    `;

    // Cache local elements
    this.triggerEl = this.shadowRoot.getElementById("trigger");
    this.panelEl = this.shadowRoot.getElementById("panel");
    this.searchEl = this.shadowRoot.getElementById("search-field");
    this.tagsEl = this.shadowRoot.getElementById("tags-container");
    this.placeholderEl = this.shadowRoot.getElementById("placeholder");
    this.chevronEl = this.shadowRoot.getElementById("chevron");
    this.optionsListEl = this.shadowRoot.getElementById("options-list");
    this.optionItems = this.shadowRoot.querySelectorAll(".ms-option");
    this.noResultsEl = this.shadowRoot.getElementById("no-results");
  }

  setupEventListeners() {
    // Open/Close Dropdown Panel
    this.triggerEl.addEventListener("click", () => this.toggleDropdown());

    // Allow triggering with space or enter when focused
    this.triggerEl.addEventListener("keydown", (e) => {
      if (e.key === " " || e.key === "Enter") {
        e.preventDefault();
        this.toggleDropdown();
      }
    });

    // Option list selections
    this.optionItems.forEach((item) => {
      item.addEventListener("click", () => {
        const val = item.getAttribute("data-value");
        this.toggleItem(val);
        this.searchEl.focus();
      });
    });

    // Realtime search text processing
    this.searchEl.addEventListener("input", (e) => {
      this.filterOptions(e.target.value);
    });

    // Stop spacebar bubbling so you can search multiple terms
    this.searchEl.addEventListener("keydown", (e) => {
      if (e.key === " ") e.stopPropagation();
    });

    // Handle clicking outside the component
    document.addEventListener("click", (e) => {
      if (!this.contains(e.target)) {
        this.toggleDropdown(false);
      }
    });
  }

  toggleDropdown(forceState = null) {
    this.isOpen = forceState !== null ? forceState : !this.isOpen;
    if (this.isOpen) {
      this.panelEl.classList.add("open");
      this.chevronEl.classList.add("rotate");
      setTimeout(() => this.searchEl.focus(), 50);
    } else {
      this.panelEl.classList.remove("open");
      this.chevronEl.classList.remove("rotate");
      this.searchEl.value = "";
      this.filterOptions("");
    }
  }

  toggleItem(val) {
    const optionItem = Array.from(this.optionItems).find(
      (i) => i.getAttribute("data-value") === val,
    );
    if (!optionItem) return;

    if (this.selectedValues.has(val)) {
      this.selectedValues.delete(val);
      optionItem.classList.remove("selected");
    } else {
      this.selectedValues.add(val);
      optionItem.classList.add("selected");
    }

    this.syncFormValue();
    this.renderTags();
  }

  filterOptions(query) {
    const cleanQuery = query.toLowerCase().trim();
    let matches = 0;

    this.optionItems.forEach((item) => {
      const name = item.getAttribute("data-name").toLowerCase();
      if (name.includes(cleanQuery)) {
        item.classList.remove("hidden");
        matches++;
      } else {
        item.classList.add("hidden");
      }
    });

    if (matches === 0) {
      this.noResultsEl.classList.remove("hidden");
    } else {
      this.noResultsEl.classList.add("hidden");
    }
  }

  // Core logic: sync dynamic state with standard Form/FormData
  syncFormValue() {
    if (this.selectedValues.size === 0) {
      this.internals.setFormValue(null);
    } else {
      // Creating FormData permits appending multiple fields under the exact same name
      const data = new FormData();
      this.selectedValues.forEach((val) => {
        data.append(this.name, val);
      });
      this.internals.setFormValue(data);
    }
  }

  renderTags() {
    this.tagsEl.innerHTML = "";

    if (this.selectedValues.size === 0) {
      this.placeholderEl.classList.remove("hidden");
    } else {
      this.placeholderEl.classList.add("hidden");
    }

    this.selectedValues.forEach((val) => {
      const itemData = this.optionsData.find((o) => o.value === val);
      if (!itemData) return;

      const pill = document.createElement("div");
      pill.className = "ms-tag";

      const labelSpan = document.createElement("span");
      labelSpan.textContent = itemData.pill;

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
        this.toggleItem(val);
      });

      pill.appendChild(labelSpan);
      pill.appendChild(closeBtn);
      this.tagsEl.appendChild(pill);
    });
  }
}

// Register Web Component with the standard custom elements registry
customElements.define("searchable-multiselect", SearchableMultiSelect);
