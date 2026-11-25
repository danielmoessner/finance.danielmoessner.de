export function ready(f) {
  if (document.readyState !== "loading") {
    f();
  } else {
    document.addEventListener("DOMContentLoaded", f);
  }
}

export function openModal(modal) {
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
