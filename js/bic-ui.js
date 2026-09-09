(function () {
  "use strict";

  document.addEventListener("click", function (event) {
    const sidebarToggle = event.target.closest("[data-bic-toggle-sidebar]");
    if (sidebarToggle) {
      const sidebar = document.querySelector(".bic-sidebar");
      if (sidebar) sidebar.classList.toggle("is-open");
    }

    const modalOpen = event.target.closest("[data-bic-modal-open]");
    if (modalOpen) {
      const id = modalOpen.getAttribute("data-bic-modal-open");
      const modal = document.getElementById(id);
      if (modal) modal.classList.add("is-open");
    }

    const modalClose = event.target.closest("[data-bic-modal-close]");
    if (modalClose) {
      const backdrop = modalClose.closest(".bic-modal-backdrop");
      if (backdrop) backdrop.classList.remove("is-open");
    }

    if (event.target.classList.contains("bic-modal-backdrop")) {
      event.target.classList.remove("is-open");
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      document.querySelectorAll(".bic-modal-backdrop.is-open")
        .forEach(el => el.classList.remove("is-open"));
    }
  });
})();
