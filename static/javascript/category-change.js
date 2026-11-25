import { ready } from "./bootstrap.js";

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
