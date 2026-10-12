# Website launch

The website is deployed at **https://curvesma.sh**, with **https://curvesmash.zac342230.chatgpt.site** also available. It is currently an owner-private preview, requiring Zac's ChatGPT login. This is separate from Yukon's pending challenge registration.

Verified deployment on 12 October 2026:

- Site: `appgprj_6acd447ed9a48191a56ad6915a49f770`
- Deployment: `appgdep_6acd460f64c08191b8d9d2b5aa6e884a`, succeeded
- Hosted source commit: `9d76707a9307fc8b3f632c148472aefe5f1fb98a`
- Static files: `dist/`, no build step or runtime secrets

## Connect curvesma.sh

The domain uses Namecheap BasicDNS. On 13 October 2026, the following records were saved and verified after reloading Namecheap's Advanced DNS page. The default apex redirect was replaced; mail settings were preserved.

| Type | Name | Value |
| --- | --- | --- |
| A | `@` | `162.159.143.30` |
| A | `@` | `172.66.3.26` |
| TXT | `_openai-site-verification` | `openai-site-verification=AZaeUIifCZmtur4ZIQoDVNkChQSqNuJb3xBoHfmOUzc` |
| TXT | `_cf-custom-hostname` | `2d03835a-3c39-424e-b230-14ba2789139c` |

These are the host's returned records for the apex domain. Both A records and the certificate verification TXT were also confirmed against Namecheap's authoritative nameserver. The host reports active domain routing and an active HTTPS certificate. A Chrome visit to https://curvesma.sh returned the expected private login page. Only the apex `curvesma.sh` is configured, without a `www` alias.

When ready for visitors, change the Site audience from owner-private to public. Domain configuration does not change access permissions. The informational website can launch before Yukon registration; keep its pending-registration notice until the platform is actually ready.

## Connect Yukon after registration

Use the actual registered challenge URL supplied by Yukon. Replace the preparation-only Participate flow with that URL only once submission, scoring and promotion checks succeed. Do not guess a Yukon challenge ID or present these organizer baselines as platform-promoted results. Keep the written guide accessible.

## Verification completed

- Desktop and mobile rendering; no page-wide horizontal overflow at 375px.
- Results/Tracks switch, target filters, chart-to-result links and both baseline detail panels.
- How it works, Review process and Participate dialogs, keyboard dismissal and focus return.
- Target-specific commands and successful clipboard copy.
- Displayed scores and memory figures checked against signed qualification records.
- No browser console errors observed; JavaScript syntax and local assets checked.
- Hosted source pushed and packaged through the Sites workflow; native deployment reports success. An unauthenticated visit shows the expected private login page.

Public access and live Yukon integration remain pending. Website-only changes leave the evaluator and mathematical evidence binding unchanged.
