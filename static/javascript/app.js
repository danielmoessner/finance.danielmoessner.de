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
  document.querySelectorAll(".modal-button").forEach((button) => {
    button.addEventListener("click", function (event) {
      const url = event.target.dataset.action;
      const modal = document.querySelector(event.target.dataset.bsTarget);
      insertFormIntoModal(modal, url);
    });
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
