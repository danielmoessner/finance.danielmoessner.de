// import '@popperjs/core/dist/umd/popper.min.js';
// import 'bootstrap/dist/js/bootstrap.min.js';
// import "@popperjs/core"
// import "bootstrap"
import { Modal } from "bootstrap";

// wrapper function that calls the submitted function as soon as the document is loaded
function ready(f) {
    if (document.readyState !== "loading") {
        f()
    } else {
        document.addEventListener('DOMContentLoaded', f)
    }
}

// put all modals to the end of the body so that they work fine on mobile
ready(function () {
    document.querySelectorAll('.modal').forEach(modal => document.body.appendChild(modal));
});

// helper
const sameUrl = (url) => url === window.location.href;

// bootstrap modal form fetch data (the form) if it is shown
ready(function () {
    document.querySelectorAll('.modal').forEach(
        modal => {
            modal.addEventListener('shown.bs.modal', function (event) {
                const url = event.target.querySelector("form").action;
                if (sameUrl(url)) return;
                const body = event.target.querySelector(".modal-body");
                if (typeof url !== "undefined" && typeof body !== "undefined") fetchAndInsert(url, body);
            })
        }
    )
    document.querySelectorAll('.modal-button').forEach(
        button => {
            button.addEventListener('click', function (event) {
                const url = event.target.dataset.action;
                const modal = document.querySelector(event.target.dataset.bsTarget);
                const form = modal.querySelector("form");
                if (url === undefined || url === "") return;
                form.action = url;
                const body = modal.querySelector(".modal-body");
                fetchAndInsert(url, body);
            })
        }
    )
});

// bootstrap form modal post the data on submit with an fetch request
ready(function () {
    document.querySelectorAll(".modal form").forEach(
        form => {
            form.addEventListener("submit", function (event) {
                event.preventDefault();
                const url = event.target.action;
                const data = new FormData(form);
                const errorElement = event.target.querySelector(".modal-body");
                const btn = form.querySelector("button[type='submit']");
                const prevBtn = btn.innerHTML;
                btn.innerHTML = `${btn.innerHTML} <svg class="animate-spin" style="width: 16px; margin-bottom: 1px; height: 16px;" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>`;
                btn.disabled = true;
                if (typeof url !== "undefined" && typeof data !== "undefined" && typeof errorElement !== "undefined")
                    postData(url, data, errorElement).finally(() => {
                        btn.innerHTML = prevBtn;
                        btn.disabled = false;
                    });
            })
        }
    )
});

// post data to an url but insert the html of the response back into an element if an error occurs
function postData(postUrl, formData, elementToInsertErrorInto) {
    return fetch(postUrl, {
        method: "post",
        body: formData,
    })
        .then((response) => {
            return response.json()
        })
        .then((data) => {
            data.valid ? window.location.reload() : elementToInsertErrorInto.innerHTML = data.html;
        })
        .catch((error) => {
            elementToInsertErrorInto.innerHTML = "Error";
        });
}

// fetches data from an url and inserts it into an element
function fetchAndInsert(urlToFetch, elementToInsertTo) {
    elementToInsertTo.innerHTML = "Loading...";
    return fetch(urlToFetch)
        .then((response) => {
            return response.text();
        })
        .then((data) => {
            elementToInsertTo.innerHTML = data;
        });
}
