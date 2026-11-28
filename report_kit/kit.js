(function () {
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var root = document.documentElement;
  if (!reduce && "IntersectionObserver" in window) root.classList.add("rk-anim");

  function countUp(el) {
    var end = parseFloat(el.getAttribute("data-count"));
    if (isNaN(end)) return;
    var decimals = (el.getAttribute("data-count").split(".")[1] || "").length;
    var start = null, dur = 900;
    function step(t) {
      if (start === null) start = t;
      var p = Math.min((t - start) / dur, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = (end * eased).toFixed(decimals);
      if (p < 1) requestAnimationFrame(step); else el.textContent = el.getAttribute("data-count");
    }
    requestAnimationFrame(step);
  }

  if (root.classList.contains("rk-anim")) {
    var seen = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.classList.add("is-in");
        e.target.querySelectorAll("[data-count]").forEach(countUp);
        seen.unobserve(e.target);
      });
    }, { threshold: 0.25 });
    document.querySelectorAll("[data-anim]").forEach(function (el) {
      el.querySelectorAll("[data-count]").forEach(function (n) { n.textContent = "0"; });
      seen.observe(el);
    });
  }

  // Filters: one active value per group ("all" shows everything); items carry data-<group> attributes
  var filterBar = document.querySelector(".rk-filters");
  if (filterBar) {
    var items = document.querySelectorAll("[data-filterable]");
    var count = filterBar.querySelector(".rk-filter-count");
    var active = {};
    function apply() {
      var shown = 0;
      items.forEach(function (it) {
        var ok = Object.keys(active).every(function (g) { return active[g] === "all" || it.getAttribute("data-" + g) === active[g]; });
        it.hidden = !ok;
        if (ok) shown++;
      });
      if (count) count.textContent = shown + " of " + items.length + " creatives";
    }
    filterBar.querySelectorAll(".rk-filter").forEach(function (group) {
      var name = group.getAttribute("data-group");
      active[name] = "all";
      group.addEventListener("click", function (ev) {
        var b = ev.target.closest("button");
        if (!b) return;
        group.querySelectorAll("button").forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
        active[name] = b.getAttribute("data-value");
        apply();
      });
    });
    apply();
  }

  // Opening a link to a collapsed creative opens it
  function openTarget() {
    var el = location.hash && document.getElementById(location.hash.slice(1));
    if (el && el.tagName === "DETAILS") { el.hidden = false; el.open = true; el.scrollIntoView(); }
  }
  window.addEventListener("hashchange", openTarget);
  openTarget();

  var links = Array.prototype.slice.call(document.querySelectorAll(".rk-toc a"));
  var sections = links.map(function (a) { return document.querySelector(a.getAttribute("href")); }).filter(Boolean);
  if ("IntersectionObserver" in window && sections.length) {
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        links.forEach(function (a) { a.classList.toggle("is-active", a.getAttribute("href") === "#" + e.target.id); });
      });
    }, { rootMargin: "-20% 0px -70% 0px" });
    sections.forEach(function (s) { spy.observe(s); });
  }
})();
