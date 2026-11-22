import { Modal } from "bootstrap";

// wrapper function that calls the submitted function as soon as the document is loaded
function ready(f) {
  if (document.readyState !== "loading") {
    f();
  } else {
    document.addEventListener("DOMContentLoaded", f);
  }
}

// put all modals to the end of the body so that they work fine on mobile
ready(function () {
  document
    .querySelectorAll(".modal")
    .forEach((modal) => document.body.appendChild(modal));
});

ready(function () {
  document
    .querySelectorAll(".category-change-bulk-button")
    .forEach((button) => {
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
  document.querySelectorAll(".modal-button").forEach((button) => {
    button.addEventListener("click", function (event) {
      const url = event.target.dataset.action;
      const modal = document.querySelector(event.target.dataset.bsTarget);
      insertFormIntoModal(modal, url);
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
    toolbar.classList.toggle("d-none", selected.length === 0);
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

function submitModalForm(form, url) {
  const data = new FormData(form);
  const errorElement = form.querySelector(".modal-body");
  const btn = form.querySelector("button[type='submit']");
  const prevBtn = btn.innerHTML;
  btn.innerHTML = `${btn.innerHTML} <svg class="animate-spin" style="width: 16px; margin-bottom: 1px; height: 16px;" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>`;
  btn.disabled = true;

  if (
    typeof url === "undefined" ||
    typeof data === "undefined" ||
    typeof errorElement === "undefined"
  )
    return;

  postData(url, data)
    .then((data) => {
      if (data.valid) {
        window.location.reload();
      } else {
        errorElement.innerHTML = data.html;
        btn.innerHTML = prevBtn;
        btn.disabled = false;
      }
    })
    .catch(() => {
      errorElement.innerHTML = "Error";
      btn.innerHTML = prevBtn;
    });
}

function submitComdirectImportForm(form, url) {
  const data = new FormData(form);
  const body = form.querySelector(".modal-body");
  const btn = form.querySelector("button[type='submit']");
  const prevBtn = btn.innerHTML;
  btn.innerHTML = `${prevBtn} <svg class="animate-spin" style="width: 16px; margin-bottom: 1px; height: 16px;" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l-2.647z"></path></svg>`;
  btn.disabled = true;

  postData(url, data)
    .then((result) => {
      if (result.valid) {
        window.location.reload();
      } else if (result.pending) {
        body.innerHTML = result.html;
        checkComdirectImport(url, data, body, btn, prevBtn, 0);
      } else {
        body.innerHTML = result.html;
        btn.innerHTML = prevBtn;
        btn.disabled = false;
      }
    })
    .catch(() => {
      showComdirectImportMessage(body, "The request failed. Please try again.");
      btn.innerHTML = prevBtn;
      btn.disabled = false;
    });
}

function checkComdirectImport(url, data, body, btn, prevBtn, attempts) {
  const maxAttempts = 60;
  if (attempts >= maxAttempts) {
    showComdirectImportMessage(
      body,
      "Still waiting for Comdirect approval. Confirm in your app, then submit to check again."
    );
    btn.innerHTML = prevBtn;
    btn.disabled = false;
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
            checkComdirectImport(url, data, body, btn, prevBtn, attempts + 1);
          } else {
            btn.innerHTML = prevBtn;
            btn.disabled = false;
          }
        }
      })
      .catch(() => {
        showComdirectImportMessage(
          body,
          "The request failed. Please submit again to continue."
        );
        btn.innerHTML = prevBtn;
        btn.disabled = false;
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
  elementToInsertTo.innerHTML = "Loading...";
  fetch(urlToFetch)
    .then((response) => {
      return response.text();
    })
    .then((data) => {
      elementToInsertTo.innerHTML = data;
    });
}
