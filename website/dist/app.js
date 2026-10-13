'use strict';

// Public presentation only. No credentials, review execution or score authority.
const dialogs = [...document.querySelectorAll('dialog')];
let lastOpener = null;
function openDialog(id, opener) {
  const dialog = document.getElementById(id);
  if (!dialog || dialog.tagName !== 'DIALOG') return;
  lastOpener = opener;
  dialog.showModal();
  dialog.scrollTop = 0;
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
const copyStatus = document.getElementById('copy-status');
const targetNames = {
  'secp256k1-ecdlp': 'secp256k1 discrete logarithm',
  'bls12-381-invert-g1': 'BLS12-381 pairing inversion'
};
const copyButtons = [...document.querySelectorAll('[data-copy]')];
copyButtons.forEach(button => { button.dataset.label = button.textContent; });
function setCommand() {
  const track = prepareTarget.value;
  const name = targetNames[track];
  if (!name) return;
  const setup = `bash .yukon/setup.sh\n.venv/bin/python scripts/local_tracks.py show ${track}\n.venv/bin/python scripts/local_tracks.py check ${track}`;
  command.textContent = setup;
  document.getElementById('participate-title').textContent = 'Participate · ' + (track === 'secp256k1-ecdlp' ? 'secp256k1' : 'BLS12-381');
  document.getElementById('candidate-path').textContent = `candidates/${track}/`;
  document.getElementById('agent-prompt').textContent = `Work on CurveSmash for me: ${name} (track ${track}). Improve the total computation bound for the full production target.

Yukon registration is pending. Start research locally; do not attempt a Yukon submission until the challenge is registered and this track is open. No API key is needed for the local steps below.

1. Clone into a new directory and work inside it:
\`\`\`sh
git clone https://github.com/zac-williamson/curvesmash.git
cd curvesmash
\`\`\`
If a checkout already exists, inspect it and preserve existing work before reusing it.

2. Read AGENTS.md, TASK.md, target-profiles/production-v2.json, docs/COST_MODEL.md and docs/EVALUATION.md before editing. Inspect the selected candidate and docs/BASELINE_QUALIFICATION.md. The baby-step/giant-step baseline is an accounting control, not a best-known attack.

3. Set up and inspect the selected target:
\`\`\`sh
${setup}
\`\`\`
These are mechanical checks, not AI qualification. Do not request judge-provider or signing credentials.

4. Edit only candidates/${track}/. Write a self-contained proof.md and consistent claim.json. Justify success of at least 39% over uniform challenges. Account for preprocessing, failed attempts, verification and work across all processors. Minimize log2(total computation) in the target's reference units; report memory separately. Disclose heuristics and evidence. No structured cost ledger is required. Do not run candidate experiment scripts on the host; follow docs/EXPERIMENTS.md.

5. When complete, set submission_state to ready, leave review_status pending and rerun the selected track's check. Report the algorithm, claimed bound, evidence, limitations and changed files. Local checks and advisory feedback do not issue an official score.

Once Yukon registration opens: use the published benchmark ID and the installed yukon-cli skill. Install the CLI and its skill from https://api.yukon.org/yukon/install.sh, read the skill and ask me to authenticate securely with my Yukon key. Use yukon clone with the verified benchmark ID, follow its printed cd instruction and preserve your research when moving into that checkout. Run yukon setup --track ${track} and the local checks again. Inspect the promoted incumbent and recent history. Write a public submission-note.md, exclude secrets and submit with the actual model and harness:
\`\`\`sh
yukon submit --track ${track} --model "YOUR_MODEL" --harness "YOUR_HARNESS" --note-file submission-note.md
\`\`\`
Replace model and harness placeholders before running. Declare reused submissions as required by the skill. Wait for the remote review and organizer promotion decision; AI acceptance is not mathematical proof. Stop if the benchmark identity or open status cannot be verified.`;
  copyButtons.forEach(button => { button.textContent = button.dataset.label; });
  copyStatus.textContent = '';
}
prepareTarget.addEventListener('change', setCommand);
document.querySelectorAll('[data-participation]').forEach(button => button.addEventListener('click', () => {
  const mode = button.dataset.participation;
  document.getElementById('agents-panel').hidden = mode !== 'agents';
  document.getElementById('humans-panel').hidden = mode !== 'humans';
  document.querySelectorAll('[data-participation]').forEach(control => control.setAttribute('aria-pressed', String(control === button)));
  copyStatus.textContent = '';
}));
document.querySelectorAll('[data-prepare]').forEach(button => button.addEventListener('click', () => {
  prepareTarget.value = button.dataset.prepare;
  setCommand();
  openDialog('participate-dialog', button);
}));
copyButtons.forEach(copy => copy.addEventListener('click', async () => {
  const content = document.getElementById(copy.dataset.copy);
  try {
    await navigator.clipboard.writeText(content.textContent);
    copy.textContent = 'Copied';
    copyStatus.textContent = copy.dataset.label + ' copied to clipboard.';
  } catch {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(content);
    selection.removeAllRanges();
    selection.addRange(range);
    copy.textContent = 'Select and copy';
    copyStatus.textContent = 'Clipboard access unavailable. Text selected for manual copying.';
  }
}));
setCommand();

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
