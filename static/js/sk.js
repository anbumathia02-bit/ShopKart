/* ============================================================
   ShopKart — front-end interactions
   • AJAX add to cart (button spinner → "Added ✓")
   • AJAX wishlist toggle (heart)
   • toast notifications
   • auto-hide flash messages
   ============================================================ */
(function () {
  "use strict";

  /* ---------------- CSRF helper ---------------- */
  function csrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.content;
    const input = document.querySelector('input[name="csrf_token"]');
    return input ? input.value : "";
  }

  /* ---------------- toasts ---------------- */
  function toast(msg, kind) {
    let stack = document.querySelector(".toast-stack");
    if (!stack) {
      stack = document.createElement("div");
      stack.className = "toast-stack";
      document.body.appendChild(stack);
    }
    const colors = { success: "#067d62", danger: "#dc2626", warning: "#b45309", info: "#1d4ed8" };
    const el = document.createElement("div");
    el.style.cssText =
      "background:" + (colors[kind] || "#111827") + ";color:#fff;padding:.7rem 1.1rem;" +
      "border-radius:12px;font-size:.88rem;font-weight:600;box-shadow:0 8px 24px rgba(0,0,0,.22);" +
      "opacity:0;transform:translateY(8px);transition:all .25s ease;max-width:min(92vw,380px)";
    el.textContent = msg;
    stack.appendChild(el);
    requestAnimationFrame(() => { el.style.opacity = "1"; el.style.transform = "translateY(0)"; });
    setTimeout(() => {
      el.style.opacity = "0"; el.style.transform = "translateY(8px)";
      setTimeout(() => el.remove(), 300);
    }, 2400);
  }
  window.skToast = toast;

  /* ---------------- cart badge ---------------- */
  function setCartCount(n) {
    document.querySelectorAll("[data-cart-count]").forEach(el => {
      el.textContent = n;
      el.style.display = n > 0 ? "" : "none";
    });
  }

  /* ---------------- AJAX add to cart ---------------- */
  document.addEventListener("submit", function (e) {
    const form = e.target;
    if (!form.matches("form[data-ajax-cart]")) return;
    e.preventDefault();

    const btn = form.querySelector("button[type=submit]") || form.querySelector("button");
    const original = btn ? btn.innerHTML : "";
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>'; }

    fetch(form.action, {
      method: "POST",
      body: new FormData(form),
      headers: { "X-Requested-With": "XMLHttpRequest" }
    })
      .then(r => r.json())
      .then(data => {
        if (data.ok) {
          setCartCount(data.cart_count);
          toast(data.msg, "success");
          if (btn) {
            btn.classList.add("btn-success", "text-white");
            btn.innerHTML = '<i class="bi bi-check2"></i> Added';
            setTimeout(() => {
              if (btn) { btn.classList.remove("btn-success", "text-white"); btn.innerHTML = original; btn.disabled = false; }
            }, 1100);
          }
          return;
        }
        toast(data.msg || "Could not add", "danger");
        if (btn) { btn.innerHTML = original; btn.disabled = false; }
      })
      .catch(() => {
        toast("Network error — try again", "danger");
        if (btn) { btn.innerHTML = original; btn.disabled = false; }
      });
  });

  /* ---------------- AJAX wishlist ---------------- */
  document.addEventListener("click", function (e) {
    const btn = e.target.closest("[data-wish]");
    if (!btn) return;
    e.preventDefault();

    fetch(btn.dataset.wish, {
      method: "POST",
      headers: { "X-Requested-With": "XMLHttpRequest", "X-CSRFToken": csrfToken() }
    })
      .then(r => r.json())
      .then(data => {
        if (data.ok) {
          btn.classList.toggle("on", data.added);
          const icon = btn.querySelector("i");
          if (icon) icon.className = data.added ? "bi bi-heart-fill" : "bi bi-heart";
          toast(data.msg, data.added ? "success" : "info");
        } else {
          toast(data.msg || "Login pannunga", "warning");
        }
      })
      .catch(() => toast("Network error", "danger"));
  });

  /* ---------------- qty box ---------------- */
  document.addEventListener("click", function (e) {
    const b = e.target.closest("[data-qty]");
    if (!b) return;
    const box = b.closest(".qtybox");
    const input = box.querySelector("input[type=number]");
    const next = Math.max(1, (parseInt(input.value, 10) || 1) + parseInt(b.dataset.qty, 10));
    input.value = next;
    const form = box.closest("form");
    if (form && form.dataset.autosubmit === "true") form.submit();
  });

  /* ---------------- auto-hide flash ---------------- */
  setTimeout(function () {
    document.querySelectorAll(".alert-auto").forEach(function (a) {
      a.style.transition = "opacity .4s";
      a.style.opacity = "0";
      setTimeout(() => a.remove(), 400);
    });
  }, 4200);

  /* ---------------- Deal-of-the-Day countdown ---------------- */
  (function () {
    const hEl = document.getElementById("cdH");
    if (!hEl) return;
    const mEl = document.getElementById("cdM");
    const sEl = document.getElementById("cdS");
    const pad = n => String(n).padStart(2, "0");
    function tick() {
      const now = new Date();
      const end = new Date(now);
      end.setHours(24, 0, 0, 0);               // tonight 12:00 AM
      let diff = Math.max(0, Math.floor((end - now) / 1000));
      hEl.textContent = pad(Math.floor(diff / 3600));
      mEl.textContent = pad(Math.floor((diff % 3600) / 60));
      sEl.textContent = pad(diff % 60);
    }
    tick();
    setInterval(tick, 1000);
  })();
})();
