# Website hosting and migration

The website is published with **GitHub Pages** from `zac-williamson/curvesmash`, using `.github/workflows/pages.yml` and `website/dist/`. The custom domain remains **https://curvesma.sh**. Visiting or publishing the static site requires no ChatGPT account or OpenAI Sites connection.

## Deployment

On 15 October 2026 (Europe/London), the user authorized migration from OpenAI Sites to GitHub Pages. [PR #1](https://github.com/zac-williamson/curvesmash/pull/1) passed both repository checks and was merged as `46e251a869895526ead8a3771f08a424513868a9`.

The [deployment](https://github.com/zac-williamson/curvesmash/actions/runs/38656702484) succeeded. Before changing DNS, anonymous HTTPS requests to `https://zac-williamson.github.io/curvesmash/` returned HTTP 200 for the homepage and all six assets. Every response matched the corresponding committed file byte for byte. Browser checks passed for opening Participate, selecting BLS12-381, switching to human instructions and closing the dialog. No browser console errors were observed.

The deployed code includes the HashSmash-style human-judge banner. The roster is empty until appointments are confirmed; no person is presented as an appointed judge by this migration.

## DNS

Namecheap BasicDNS continues to manage the domain. The following apex records replaced the former hosting addresses and were confirmed after reloading Namecheap:

| Type | Host | Value | TTL |
| --- | --- | --- | --- |
| A | `@` | `185.199.108.153` | 1 minute |
| A | `@` | `185.199.109.153` | 1 minute |
| A | `@` | `185.199.110.153` | 1 minute |
| A | `@` | `185.199.111.153` | 1 minute |

The custom domain was bound to the GitHub Pages repository before the DNS cutover. Authoritative DNS and Google and Cloudflare public DNS returned all four GitHub addresses. Existing TXT records and email forwarding were preserved. Only the apex domain is configured; no `www` hostname was added.

GitHub issued a certificate for `curvesma.sh`, expiring 12 January 2027, and HTTPS enforcement is enabled. The [final deployment](https://github.com/zac-williamson/curvesmash/actions/runs/38657365473) succeeded with the custom-domain configuration.

Anonymous HTTPS requests using the addresses returned by authoritative and public DNS verified the homepage and all six assets byte for byte against the deployed source. TLS certificate validation succeeded on all four GitHub addresses, and HTTP returned a 301 redirect to `https://curvesma.sh/`. The verifier disabled local curl configuration and supplied no cookies or authorization. The browser loaded the new version at the custom domain without a sign-in page or console errors; its judge-display markup and canonical URL were checked.

The operator's local system resolver still cached the old hosting addresses during verification, while authoritative DNS, Google DNS, Cloudflare DNS and the browser used the new addresses. Existing cached visitors may continue reaching the old deployment until their DNS cache expires. The old host remains active during propagation. The saved local verification report records that distinction rather than treating cached old content as the new deployment.

## Publishing and rollback

Merge website changes into `main`; the workflow automatically deploys changes to `website/dist/`. It can also be dispatched manually. The deployment uses GitHub's short-lived token, with no repository deployment secrets or external build service.

For an application regression, revert the website change and let the same workflow deploy it. During this migration the original OpenAI Sites deployment remains available at `https://curvesmash.zac342230.chatgpt.site/`. The former apex A records were `162.159.143.30` and `172.66.3.26`; restoring those records would route traffic back to that host while its domain configuration remains active.

## Previous hosting record

The former OpenAI Sites project was `appgprj_6acd447ed9a48191a56ad6915a49f770`. Its last verified deployment was `appgdep_6acd76a50e0481919a73176f1312cc5c`, from hosted source `12f9ac98397b46d988ada0f78373f5c0617cdf86`, on 13 October 2026. It was made public at the user's request and verified without login. On 15 October the native publishing connector could no longer retrieve that project, although the signed-in owner could still see its settings. GitHub Pages replaces this publishing dependency.

The retained old verification TXT records are `_openai-site-verification` and `_cf-custom-hostname`. They are historical hosting records, not requirements for GitHub Pages. The previous deployment checkout `/Users/zac/curvesmash-site` is historical and should not be used for current publication.

Yukon registration, human reviewer grants and submission readiness are separate from website hosting. This migration does not change the evaluator, targets, cost rules, baselines or promotion policy.
