import $ from 'jquery';
window.jQuery = $;
window.$ = $;
import 'popper.js';
import 'bootstrap';

// put all modals to the end of the body so that they work fine on mobile
$(window).on('load', function () {
    $(".modal").appendTo("body")
});

// bootstrap modal form fetch data (the form) if it is shown
$(window).on('load', function () {
    $(".modal").on('show.bs.modal', function (event) {
        const url = $(event.target).find("form").attr('action');
        const body = $(event.target).find(".modal-body");
        if (typeof url !== "undefined" && typeof body !== "undefined") fetchAndInsert(url, body);
    })
});

// bootstrap form modal post the data on submit with an fetch request
$(window).on('load', function () {
    $(".modal form").on("submit", function (event) {
        event.preventDefault();
        const url = $(event.target).attr('action');
        const data = $(event.target).serialize();
        const errorElement = $(event.target).find(".modal-body");
        if (typeof url !== "undefined" && typeof data !== "undefined" && typeof errorElement !== "undefined")
            postData(url, data, errorElement);
    });
});

// post data to an url but insert the html of the response back into an element if an error occurs
function postData(postUrl, formData, elementToInsertErrorInto) {
    fetch(postUrl, {
        method: "post",
        body: formData,
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    })
        .then((response) => {
            return response.json()
        })
        .then((data) => {
            data.valid ? window.location.reload() : $(elementToInsertErrorInto).html(data.html);
        })
        .catch((error) => {
            $(elementToInsertErrorInto).html("Error");
        });
}

// fetches data from an url and inserts it into an element
function fetchAndInsert(urlToFetch, elementToInsertTo) {
    fetch(urlToFetch)
        .then((response) => {
            return response.text();
        })
        .then((data) => {
            elementToInsertTo.html(data);
        });
}
