const toggle = document.querySelector('.menu-toggle');
const links = document.querySelector('.nav-links');
const tabs = document.querySelectorAll('.profile-tab');
const panels = document.querySelectorAll('[data-panel-content]');

function selectPanel(name) {
  tabs.forEach((tab) => {
    const selected = tab.dataset.panel === name;
    tab.classList.toggle('is-active', selected);
    tab.setAttribute('aria-selected', String(selected));
  });
  panels.forEach((panel) => {
    const selected = panel.dataset.panelContent === name;
    panel.hidden = !selected;
    if (selected) {
      panel.classList.remove('is-turning');
      void panel.offsetWidth;
      panel.classList.add('is-turning');
    }
  });
}

toggle?.addEventListener('click', () => {
  const open = links.classList.toggle('is-open');
  toggle.setAttribute('aria-expanded', String(open));
});

links?.addEventListener('click', (event) => {
  const target = event.target.closest('[data-panel-target]');
  if (target) selectPanel(target.dataset.panelTarget);
  if (event.target.matches('a') && links.classList.contains('is-open')) {
    links.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
  }
});

tabs.forEach((tab) => tab.addEventListener('click', () => selectPanel(tab.dataset.panel)));

document.querySelector('#year').textContent = new Date().getFullYear();
