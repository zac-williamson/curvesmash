'use strict';

// Public presentation only. No credentials, review execution or score authority.
const dialogs = [...document.querySelectorAll('dialog')];
let lastOpener = null;
function openDialog(id, opener) {
  const dialog = document.getElementById(id);
  if (!dialog || dialog.tagName !== 'DIALOG') return;
  lastOpener = opener;
  dialog.showModal();
}
document.querySelectorAll('[data-open]').forEach(button => {
  button.addEventListener('click', () => openDialog(button.dataset.open, button));
});
dialogs.forEach(dialog => {
  dialog.querySelector('[data-close]').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => {
    const r = dialog.getBoundingClientRect();
    if (event.target === dialog && (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom)) dialog.close();
  });
  dialog.addEventListener('close', () => { if (lastOpener) lastOpener.focus(); });
});

function setView(view) {
  document.getElementById('results-view').hidden = view !== 'results';
  document.getElementById('tracks-view').hidden = view !== 'tracks';
  document.querySelectorAll('[data-view]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.view === view)));
  document.getElementById('results-title').textContent = view === 'results' ? 'Published baselines' : 'Research targets';
}
document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => setView(button.dataset.view)));
const filter = document.getElementById('target-filter');
function filterRows() {
  document.querySelectorAll('tr[data-track]').forEach(row => { row.hidden = filter.value !== 'all' && row.dataset.track !== filter.value; });
}
filter.addEventListener('change', filterRows);
document.querySelectorAll('[data-result]').forEach(button => button.addEventListener('click', event => {
  event.preventDefault();
  setView('results');
  filter.value = button.dataset.result;
  filterRows();
  document.getElementById('results').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'});
  filter.focus({preventScroll:true});
}));

const prepareTarget = document.getElementById('prepare-target');
const command = document.getElementById('prepare-command');
const copy = document.getElementById('copy-command');
const copyStatus = document.getElementById('copy-status');
function setCommand() {
  command.textContent = 'git clone https://github.com/zac-williamson/curvesmash.git\ncd curvesmash\nbash .yukon/setup.sh\n.venv/bin/python scripts/local_tracks.py check ' + prepareTarget.value;
  document.getElementById('candidate-path').textContent = 'candidates/' + prepareTarget.value;
  copy.textContent = 'Copy commands';
  copyStatus.textContent = '';
}
prepareTarget.addEventListener('change', setCommand);
document.querySelectorAll('[data-prepare]').forEach(button => button.addEventListener('click', () => {
  prepareTarget.value = button.dataset.prepare;
  setCommand();
  openDialog('participate-dialog', button);
}));
copy.addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(command.textContent);
    copy.textContent = 'Copied';
    copyStatus.textContent = 'Commands copied to clipboard.';
  } catch {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(command);
    selection.removeAllRanges();
    selection.addRange(range);
    copy.textContent = 'Select and copy';
    copyStatus.textContent = 'Clipboard access unavailable. Commands selected for manual copying.';
  }
});

// An original elliptic-curve constellation, echoing HashSmash's blue graphic.
// This is an illustration, not a depiction of the production finite groups.
const svgNS = 'http://www.w3.org/2000/svg';
const stars = document.getElementById('stars');
const connections = document.getElementById('connections');
function svgElement(name, attributes, parent) {
  const element = document.createElementNS(svgNS, name);
  Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, String(value)));
  parent.appendChild(element);
}
const points = [];
for (let i = 0; i < 46; i++) {
  const x = -1.77 + i * 0.086;
  const square = x * x * x - 2 * x + 3;
  if (square < 0) continue;
  const y = Math.sqrt(square);
  for (const sign of [-1,1]) points.push([110 + (x + 1.8)*205, 185 + sign*y*35]);
}
points.forEach(([x,y], i) => {
  const bright = i % 13 === 0;
  if (i+2 < points.length) svgElement('line', {x1:x,y1:y,x2:points[i+2][0],y2:points[i+2][1],class:'connection'}, connections);
  if (i % 7 === 0) {
    const next = points[(i+29)%points.length];
    svgElement('line',{x1:x,y1:y,x2:next[0],y2:next[1],class:'connection'},connections);
  }
  if (bright) svgElement('circle',{cx:x,cy:y,r:8,class:'halo'},stars);
  svgElement('circle',{cx:x,cy:y,r:bright ? 2.5 : 1.3,class:'star',opacity:bright ? 1 : .55+(i%3)*.15},stars);
});
