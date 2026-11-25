export function setupComdirectImport({ postData, ready, setButtonBusy }) {
  ready(function () {
    document.querySelectorAll(".comdirect-import-form").forEach((form) => {
      form.addEventListener("submit", function (event) {
        event.preventDefault();
        submitComdirectImportForm(form, event.target.action);
      });
    });
  });

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
}

function showComdirectImportMessage(body, message) {
  const csrfField = body.querySelector("input[name='csrfmiddlewaretoken']");
  body.textContent = message;
  if (csrfField) {
    body.appendChild(csrfField);
  }
}
