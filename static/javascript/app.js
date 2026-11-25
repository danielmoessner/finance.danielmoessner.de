import { openModal, ready } from "./bootstrap.js";
import "./category-change.js";
import { setupComdirectImport } from "./comdirect-import.js";

const spinner =
  '<svg class="inline-block h-4 w-4 shrink-0 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>';

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

function postData(postUrl, formData) {
  return fetch(postUrl, {
    method: "post",
    body: formData,
  }).then((response) => {
    return response.json();
  });
}

ready(function () {
  document.addEventListener("click", function (event) {
    const opener = event.target.closest("[data-modal-target]");
    if (!opener) return;
    event.preventDefault();
    const modal = document.querySelector(opener.dataset.modalTarget);
    if (!modal) return;
    insertFormIntoModal(modal, opener.dataset.action);
    openModal(modal);
  });
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
    if (form.classList.contains("comdirect-import-form")) return;
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      submitModalForm(form, event.target.action);
    });
  });
});

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

setupComdirectImport({ postData, ready, setButtonBusy });

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
