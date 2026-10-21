# CurveSmash domain redirect

`https://curvesma.sh` redirects visitors to `https://yukon.org/curvesmash`.
The existing GitHub Pages deployment retains the domain and HTTPS certificate;
Eigen Labs hosts the challenge UI. No DNS change is needed.

`dist/index.html` provides immediate meta refresh plus an accessible fallback
link. `dist/app.js` uses `location.replace` so Back does not return to the
redirect. This is a browser redirect, not an HTTP 301 response.

Edit `website/dist/` and push to `main`; the Publish website workflow deploys it.
The previous site remains available in Git history.
