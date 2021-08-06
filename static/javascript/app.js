import 'bootstrap';

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

// bootstrap modal form fetch data (the form) if it is shown
ready(function () {
    document.querySelectorAll('.modal').forEach(
        modal => {
            modal.addEventListener('shown.bs.modal', function (event) {
                const url = event.target.querySelector("form").action;
                const body = event.target.querySelector(".modal-body");
                if (typeof url !== "undefined" && typeof body !== "undefined") fetchAndInsert(url, body);
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
    fetch(urlToFetch)
        .then((response) => {
            return response.text();
        })
        .then((data) => {
            elementToInsertTo.innerHTML = data;
        });
}
