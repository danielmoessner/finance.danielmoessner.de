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
                if (typeof url !== "undefined" && typeof data !== "undefined" && typeof errorElement !== "undefined")
                    postData(url, data, errorElement);
            })
        }
    )
});

// post data to an url but insert the html of the response back into an element if an error occurs
function postData(postUrl, formData, elementToInsertErrorInto) {
    fetch(postUrl, {
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
    fetch(urlToFetch)
        .then((response) => {
            return response.text();
        })
        .then((data) => {
            elementToInsertTo.innerHTML = data;
        });
}
