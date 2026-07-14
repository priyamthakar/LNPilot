// Minimal vanilla JS for the LNPilot UI: pill/segmented toggles, accordion, tabs.
// No frameworks — form fields are plain <input>s; toggles just update a hidden
// input's value and restyle the pressed button before native form submit.

document.addEventListener("click", function (e) {
  var toggle = e.target.closest("[data-toggle-group]");
  if (toggle) {
    var group = toggle.getAttribute("data-toggle-group");
    var value = toggle.getAttribute("data-value");
    document
      .querySelectorAll('[data-toggle-group="' + group + '"]')
      .forEach(function (btn) {
        btn.classList.toggle("active", btn === toggle);
      });
    var hidden = document.querySelector('input[type="hidden"][name="' + group + '"]');
    if (hidden) hidden.value = value;
    return;
  }

  var accHead = e.target.closest(".accordion-head");
  if (accHead) {
    accHead.closest(".accordion").classList.toggle("open");
    return;
  }

  var tab = e.target.closest("[data-tab]");
  if (tab) {
    var tabGroup = tab.closest(".tabs");
    var panelId = tab.getAttribute("data-tab");
    tabGroup.querySelectorAll(".tab").forEach(function (t) {
      t.classList.toggle("active", t === tab);
    });
    document.querySelectorAll("[data-tab-panel]").forEach(function (panel) {
      panel.classList.toggle("active", panel.getAttribute("data-tab-panel") === panelId);
    });
  }
});
