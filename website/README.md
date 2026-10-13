# CurveSmash website

A standalone static page following the presentation of [HashSma.sh](https://hashsma.sh), which redirects to Yukon's HashSmash challenge page. The HTML, styling and elliptic-curve illustration are original; no HashSmash source, proprietary fonts, partner logos or judge identities are copied.

The page presents exactly two full-production targets and the verified version 2 baselines. Results are a published snapshot, not a live Yukon leaderboard. Registration is pending and no submit endpoint is exposed. Participate offers a target-specific, copyable agent prompt and numbered human instructions. Local research starts without API keys. Once Yukon registers the challenge, add its verified benchmark identity and live clone/submission instructions to this flow.

## Preview

From the repository root:

```sh
python3 -m http.server 4173 --bind 127.0.0.1 --directory website/dist
```

Open `http://127.0.0.1:4173`. No build tools, package installation, API keys or external asset services are needed. Deploy the contents of `dist/` with any static host.

## Evidence and updates

The displayed scores and result details come from the [v0.2.0 qualification record](../docs/BASELINE_QUALIFICATION.md). Links point to the exact baseline source commit, signed review runs and durable evidence release. Publish new results only from authenticated qualification records; do not label an AI-reviewed baseline as human accepted or Yukon promoted.

Website files are outside participant editable paths and the evaluator's evidence binding. Styling and website-only updates do not require new mathematical reviews. This page has no tracking, account flow, third-party fonts or browser-side provider access. The participation, privacy and review links point to the public repository policies.

The Sites deployment checkout is `/Users/zac/curvesmash-site`, separate from this benchmark repository. Its `.openai/hosting.json` records the registered Site identity and `dist` output. Copy this `dist/` exactly when updating that checkout; use the Sites publishing workflow to commit, push, package and deploy the same bytes. Keep private source credentials outside both repositories.
