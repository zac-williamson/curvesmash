# Website launch

The website is public at **https://curvesma.sh**, with **https://curvesmash.zac342230.chatgpt.site** also available. No login or ChatGPT account is required. This is separate from Yukon's pending challenge registration.

Verified deployment on 13 October 2026:

- Site: `appgprj_6acd447ed9a48191a56ad6915a49f770`
- Deployment: `appgdep_6acd76a50e0481919a73176f1312cc5c`, succeeded
- Hosted source commit: `12f9ac98397b46d988ada0f78373f5c0617cdf86`
- Static files: `dist/`, no build step or runtime secrets

## Connect curvesma.sh

The domain uses Namecheap BasicDNS. On 13 October 2026, the following records were saved and verified after reloading Namecheap's Advanced DNS page. The default apex redirect was replaced; mail settings were preserved.

| Type | Name | Value |
| --- | --- | --- |
| A | `@` | `162.159.143.30` |
| A | `@` | `172.66.3.26` |
| TXT | `_openai-site-verification` | `openai-site-verification=AZaeUIifCZmtur4ZIQoDVNkChQSqNuJb3xBoHfmOUzc` |
| TXT | `_cf-custom-hostname` | `2d03835a-3c39-424e-b230-14ba2789139c` |

These are the host's returned records for the apex domain. Both A records and the certificate verification TXT were also confirmed against Namecheap's authoritative nameserver. The host reports active domain routing and an active HTTPS certificate. Only the apex `curvesma.sh` is configured, without a `www` alias.

On 13 October 2026, the Site audience was changed to public at Zac's request. Anonymous requests with no cookies or authentication returned HTTP 200 for the homepage, stylesheet, JavaScript and icon, without redirecting to sign-in. The homepage displayed both targets and qualified baseline scores; the three checked assets matched the published source exactly. A browser reload also displayed the homepage without sign-in. Keep the pending-registration notice until Yukon is actually ready.

## Connect Yukon after registration

Use the actual registered challenge URL supplied by Yukon. Replace the preparation-only Participate flow with that URL only once submission, scoring and promotion checks succeed. Do not guess a Yukon challenge ID or present these organizer baselines as platform-promoted results. Keep the written guide accessible.

## Verification completed

- Desktop and mobile rendering; no page-wide horizontal overflow at 375px.
- Results/Tracks switch, target filters, chart-to-result links and both baseline detail panels.
- How it works, Review process and Participate dialogs, keyboard dismissal and focus return.
- For agents / For humans participation modes; numbered steps, target-specific full agent prompts and successful clipboard copying of prompts and commands.
- Displayed scores and memory figures checked against signed qualification records.
- No browser console errors observed; JavaScript syntax and local assets checked.
- Hosted source pushed and packaged through the Sites workflow; native deployment reports success. Public access was confirmed by the host and verified with anonymous HTTP requests and a browser visit.

Live Yukon integration remains pending. Website-only changes leave the evaluator and mathematical evidence binding unchanged.
