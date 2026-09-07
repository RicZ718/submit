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

/* ===== 浅色 / 深色主题切换（默认浅色） ===== */
const themeToggle = document.querySelector('#theme-toggle');
const rootEl = document.documentElement;

function paintThemeToggle() {
  if (!themeToggle) return;
  const dark = rootEl.classList.contains('theme-dark');
  themeToggle.textContent = dark ? '☀️ 浅色' : '🌙 深色';
  themeToggle.setAttribute('aria-pressed', String(dark));
  const label = dark ? '切换到浅色模式' : '切换到深色模式';
  themeToggle.setAttribute('aria-label', label);
  themeToggle.title = label;
}

function applyTheme(dark) {
  rootEl.classList.toggle('theme-dark', dark);
  paintThemeToggle();
}

function savedTheme() {
  try { return localStorage.getItem('page-theme'); } catch { return null; }
}

applyTheme(savedTheme() === 'dark');

themeToggle?.addEventListener('click', () => {
  const dark = !rootEl.classList.contains('theme-dark');
  applyTheme(dark);
  try { localStorage.setItem('page-theme', dark ? 'dark' : 'light'); } catch { /* ignore */ }
});

/* ===== 着陆页：点击“查看资料”后退出全屏壁纸并显示资料界面 ===== */
const viewProfileBtn = document.querySelector('a.button[href="#profile"]');

function enterSite(shouldScroll = true) {
  const wasLanding = document.body.classList.contains('is-landing');
  if (wasLanding) {
    document.body.classList.remove('is-landing');
    // 等 hero 收缩动画结束后再平滑滚动到资料区
    if (shouldScroll) {
      setTimeout(() => {
        document.getElementById('profile')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 800);
    }
  } else if (shouldScroll) {
    document.getElementById('profile')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

viewProfileBtn?.addEventListener('click', (event) => {
  event.preventDefault();
  enterSite();
});
