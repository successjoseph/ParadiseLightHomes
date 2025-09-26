// script.js

// Cookie Banner
const cookieBanner = document.getElementById("cookie-banner");
const acceptBtn = document.getElementById("accept-cookies");

if (cookieBanner && acceptBtn && !localStorage.getItem("cookiesAccepted")) {
  cookieBanner.classList.remove("hidden");
  acceptBtn.addEventListener("click", () => {
    localStorage.setItem("cookiesAccepted", "yes");
    cookieBanner.classList.add("hidden");
  });
}


// Mobile Menu Toggle
window.toggleMenu = function () {
  const menu = document.getElementById("nav-menu");
  const icon = document.getElementById("menu-icon");
  const btn = event?.currentTarget || null;

  if (!menu || !icon) return;

  const isOpen = !menu.classList.contains("hidden");

  if (isOpen) {
    // closing
    menu.classList.remove("slide-down");
    menu.classList.add("slide-up");
    icon.classList.remove("active");
    if (btn) btn.setAttribute('aria-expanded', 'false');
    setTimeout(() => menu.classList.add("hidden"), 300);
  } else {
    // opening
    menu.classList.remove("hidden", "slide-up");
    menu.classList.add("slide-down");
    icon.classList.add("active");
    if (btn) btn.setAttribute('aria-expanded', 'true');
  }
};

// Auto-close nav on link click
document.querySelectorAll("#nav-menu a").forEach(link => {
  link.addEventListener("click", () => {
    const menu = document.getElementById("nav-menu");
    if (!menu.classList.contains("hidden")) {
      menu.classList.replace("slide-down", "slide-up");
      setTimeout(() => menu.classList.add("hidden"), 300);
    }
  });
});

// ROI Calculator (Area → Yield)
function calculateROI() {
  const areaEl = document.getElementById("area");
  const unitEl = document.getElementById("unit");
  const resultEl = document.getElementById("roi-result");

  if (!areaEl || !unitEl || !resultEl) return;

  const areaInput = parseFloat(areaEl.value);
  const unit = unitEl.value;

  if (isNaN(areaInput) || areaInput <= 0) {
    resultEl.textContent = "Please enter a valid number.";
    resultEl.style.color = "red";
    return;
  }

  const PLOTS_PER_ACRE = 6;
  const ACRES_PER_HECTARE = 2.5;
  const PLOTS_PER_HECTARE = PLOTS_PER_ACRE * ACRES_PER_HECTARE;
  const yieldPerPlot = 150; // hardcoded

  let areaInPlots;
  switch (unit) {
    case "hectares": areaInPlots = areaInput * PLOTS_PER_HECTARE; break;
    case "acres": areaInPlots = areaInput * PLOTS_PER_ACRE; break;
    default: areaInPlots = areaInput;
  }

  const baseYield = areaInPlots * yieldPerPlot;
  const minYield = Math.round(baseYield * 0.64);
  const maxYield = Math.round(baseYield);

  resultEl.textContent = 
    `Estimated Yield: ${minYield.toLocaleString()} – ${maxYield.toLocaleString()} litres`;
  resultEl.style.color = "green";
}


// Contact Form
const contactForm = document.getElementById("contact-form");
if (contactForm) {
  contactForm.addEventListener("submit", function (e) {
    e.preventDefault();

    let confirmation = document.getElementById("form-confirmation");
    if (!confirmation) {
      confirmation = document.createElement("div");
      confirmation.id = "form-confirmation";
      confirmation.style.color = "green";
      confirmation.style.marginTop = "8px";
      contactForm.appendChild(confirmation);
    }
    confirmation.textContent = "✅ Your message has been sent. We'll contact you soon.";
  });
}

document.addEventListener('DOMContentLoaded', async () => {
  await loadContent(); // your existing loader
  document.querySelectorAll('.card').forEach((el, i) => {
    setTimeout(() => el.classList.add('visible'), i * 40); // stagger, optional
  });
});

