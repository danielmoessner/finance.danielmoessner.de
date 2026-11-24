const spinner =
  '<svg class="inline-block h-4 w-4 shrink-0 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>';

function ready(f) {
  if (document.readyState !== "loading") {
    f();
  } else {
    document.addEventListener("DOMContentLoaded", f);
  }
}

function openModal(modal) {
  document.querySelectorAll(".modal.is-open").forEach((open) => {
    if (open !== modal) closeModal(open);
  });
  closeDropdowns();
  modal.classList.add("is-open");
  document.body.classList.add("overflow-hidden");
}

function closeModal(modal) {
  modal.classList.remove("is-open");
  if (!document.querySelector(".modal.is-open")) {
    document.body.classList.remove("overflow-hidden");
  }
}

function closeDropdowns() {
  document.querySelectorAll(".dropdown-menu.is-open").forEach((menu) => {
    menu.classList.remove("is-open");
  });
  document.querySelectorAll("[data-dropdown-toggle]").forEach((toggle) => {
    toggle.setAttribute("aria-expanded", "false");
  });
}

function placeDropdown(toggle, menu) {
  const rect = toggle.getBoundingClientRect();
  const width = Math.max(rect.width, 160);
  let left = rect.right - width;
  if (left < 8) left = 8;
  if (left + width > window.innerWidth - 8) {
    left = Math.max(8, window.innerWidth - 8 - width);
  }
  menu.style.top = `${rect.bottom + 4}px`;
  menu.style.left = `${left}px`;
}

ready(function () {
  document.querySelectorAll(".modal").forEach((modal) => {
    document.body.appendChild(modal);
  });
});

ready(function () {
  document.querySelectorAll(".category-change-bulk-button").forEach((button) => {
    button.addEventListener(
      "click",
      function () {
        const selectedIds = Array.from(
          document.querySelectorAll(".category-change-selection:checked"),
        ).map((checkbox) => checkbox.value);
        const actionUrl = new URL(button.dataset.action, window.location.href);
        actionUrl.searchParams.set("changes", selectedIds.join(","));
        button.dataset.action = actionUrl.pathname + actionUrl.search;
      },
      { capture: true },
    );
  });
});

ready(function () {
  document.addEventListener("click", function (event) {
    const toggle = event.target.closest("[data-dropdown-toggle]");
    if (toggle) {
      event.preventDefault();
      const menu = toggle.parentElement.querySelector("[data-dropdown-menu]");
      const willOpen = menu && !menu.classList.contains("is-open");
      closeDropdowns();
      if (willOpen) {
        placeDropdown(toggle, menu);
        menu.classList.add("is-open");
        toggle.setAttribute("aria-expanded", "true");
      }
      return;
    }

    if (!event.target.closest("[data-dropdown-menu]")) {
      closeDropdowns();
    }

    const opener = event.target.closest("[data-modal-target]");
    if (opener) {
      event.preventDefault();
      const modal = document.querySelector(opener.dataset.modalTarget);
      if (!modal) return;
      insertFormIntoModal(modal, opener.dataset.action);
      openModal(modal);
      return;
    }

    if (event.target.closest("[data-dismiss='modal']")) {
      const modal = event.target.closest(".modal");
      if (modal) closeModal(modal);
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    closeDropdowns();
    document.querySelectorAll(".modal.is-open").forEach(closeModal);
  });

  window.addEventListener("resize", closeDropdowns);
  window.addEventListener("scroll", closeDropdowns, true);

  document.querySelectorAll("[data-nav-toggle]").forEach((button) => {
    button.addEventListener("click", function () {
      const nav = document.getElementById(button.getAttribute("aria-controls"));
      if (!nav) return;
      const collapsed = nav.classList.toggle("hidden");
      button.setAttribute("aria-expanded", collapsed ? "false" : "true");
    });
  });
});

ready(function () {
  const checkboxes = Array.from(
    document.querySelectorAll(".category-change-selection"),
  );
  const selectAll = document.querySelector(".category-change-select-all");
  const toolbar = document.querySelector(".category-change-toolbar");
  if (!checkboxes.length || !selectAll || !toolbar) return;

  const updateSelection = () => {
    const selected = checkboxes.filter((checkbox) => checkbox.checked);
    const sumInCents = selected.reduce(
      (total, checkbox) =>
        total + Math.round(Number(checkbox.dataset.amount) * 100),
      0,
    );
    toolbar.classList.toggle("hidden", selected.length === 0);
    toolbar.querySelector(".category-change-selection-count").textContent =
      `${selected.length} selected`;
    toolbar.querySelector(".category-change-selection-sum").textContent =
      `${new Intl.NumberFormat("de-DE", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(sumInCents / 100)} €`;
    selectAll.checked = selected.length === checkboxes.length;
    selectAll.indeterminate =
      selected.length > 0 && selected.length < checkboxes.length;
  };

  checkboxes.forEach((checkbox) => {
    checkbox.addEventListener("change", updateSelection);
  });
  selectAll.addEventListener("change", () => {
    checkboxes.forEach((checkbox) => {
      checkbox.checked = selectAll.checked;
    });
    updateSelection();
  });
  updateSelection();
});

function insertFormIntoModal(modal, url) {
  const form = modal.querySelector("form");
  const btn = form.querySelector("button[type='submit']");
  btn.disabled = false;
  if (url === undefined || url === "") return;
  form.action = url;
  const body = modal.querySelector(".modal-body");
  fetchAndInsert(url, body);
}

ready(function () {
  document.querySelectorAll(".modal form").forEach((form) => {
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      if (form.classList.contains("comdirect-import-form")) {
        submitComdirectImportForm(form, event.target.action);
      } else {
        submitModalForm(form, event.target.action);
      }
    });
  });
});

function setButtonBusy(btn, busy) {
  if (busy) {
    btn.dataset.prevHtml = btn.innerHTML;
    btn.innerHTML = `${btn.dataset.prevHtml} ${spinner}`;
    btn.disabled = true;
    return;
  }
  btn.innerHTML = btn.dataset.prevHtml || btn.innerHTML;
  btn.disabled = false;
}

function submitModalForm(form, url) {
  const data = new FormData(form);
  const errorElement = form.querySelector(".modal-body");
  const btn = form.querySelector("button[type='submit']");

  if (
    typeof url === "undefined" ||
    typeof data === "undefined" ||
    typeof errorElement === "undefined"
  )
    return;

  setButtonBusy(btn, true);

  postData(url, data)
    .then((data) => {
      if (data.valid) {
        window.location.reload();
      } else {
        errorElement.innerHTML = data.html;
        setButtonBusy(btn, false);
      }
    })
    .catch(() => {
      errorElement.innerHTML = "Error";
      setButtonBusy(btn, false);
    });
}

function submitComdirectImportForm(form, url) {
  const data = new FormData(form);
  const body = form.querySelector(".modal-body");
  const btn = form.querySelector("button[type='submit']");
  setButtonBusy(btn, true);

  postData(url, data)
    .then((result) => {
      if (result.valid) {
        window.location.reload();
      } else if (result.pending) {
        body.innerHTML = result.html;
        checkComdirectImport(url, data, body, btn, 0);
      } else {
        body.innerHTML = result.html;
        setButtonBusy(btn, false);
      }
    })
    .catch(() => {
      showComdirectImportMessage(body, "The request failed. Please try again.");
      setButtonBusy(btn, false);
    });
}

function checkComdirectImport(url, data, body, btn, attempts) {
  const maxAttempts = 60;
  if (attempts >= maxAttempts) {
    showComdirectImportMessage(
      body,
      "Still waiting for Comdirect approval. Confirm in your app, then submit to check again.",
    );
    setButtonBusy(btn, false);
    return;
  }

  window.setTimeout(() => {
    postData(url, data)
      .then((result) => {
        if (result.valid) {
          window.location.reload();
        } else {
          body.innerHTML = result.html;
          if (result.pending) {
            checkComdirectImport(url, data, body, btn, attempts + 1);
          } else {
            setButtonBusy(btn, false);
          }
        }
      })
      .catch(() => {
        showComdirectImportMessage(
          body,
          "The request failed. Please submit again to continue.",
        );
        setButtonBusy(btn, false);
      });
  }, 1000);
}

function showComdirectImportMessage(body, message) {
  const csrfField = body.querySelector("input[name='csrfmiddlewaretoken']");
  body.textContent = message;
  if (csrfField) {
    body.appendChild(csrfField);
  }
}

function postData(postUrl, formData) {
  return fetch(postUrl, {
    method: "post",
    body: formData,
  }).then((response) => {
    return response.json();
  });
}

function fetchAndInsert(urlToFetch, elementToInsertTo) {
  elementToInsertTo.textContent = "Loading...";
  fetch(urlToFetch)
    .then((response) => {
      return response.text();
    })
    .then((data) => {
      elementToInsertTo.innerHTML = data;
      const field = elementToInsertTo.querySelector(
        "input:not([type='hidden']), select, textarea",
      );
      if (field) field.focus();
    });
}
