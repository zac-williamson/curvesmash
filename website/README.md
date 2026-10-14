# CurveSmash website

The public website is a static page at **https://curvesma.sh**, published with GitHub Pages from `zac-williamson/curvesmash`. No account, API key or runtime service is needed to visit it.

The presentation follows [HashSmash](https://www.yukon.org/hashsmash). It shows exactly two production targets and the signed version 2 baseline results. The displayed results are a published snapshot, not a live Yukon leaderboard.

## Publish

Edit `website/dist/` and merge into `main`. [Publish website](../.github/workflows/pages.yml) deploys that directory through GitHub Actions. It uses GitHub's short-lived deployment identity and requires no repository deployment secret. A manual dispatch can redeploy `main`.

The Pages custom domain is configured in the repository's Pages settings. Namecheap manages DNS. See [LAUNCH.md](LAUNCH.md) for the migration record and verification.

## Human judges

Like HashSmash, **Meet the Judges** opens a banner of names and affiliations. `dist/judges.json` contains only appointed human judges, as objects with `name` and `affiliation`. The roster is empty until appointments are confirmed; the button and banner stay hidden for an empty or unavailable roster. Add confirmed names and publish normally. This display does not grant Yukon reviewer permissions or change the review policy.

## Preview

From the repository root:

```sh
python3 -m http.server 4173 --bind 127.0.0.1 --directory website/dist
```

Open `http://127.0.0.1:4173`. No build or package installation is required. Local assets use relative URLs so the same files work on the custom domain and the GitHub Pages project URL. GitHub Pages does not consume `_headers`; the HTML supplies the content security and referrer policies supported through metadata.

## Evidence

Scores and result details come from the [v0.2.0 qualification record](../docs/BASELINE_QUALIFICATION.md). Links preserve the exact baseline source, signed review runs and evidence release. Publish new results only from authenticated records; do not label an AI-reviewed baseline as human accepted or Yukon promoted.

Website files remain outside participant editable paths and the evaluator's evidence binding. This site has no account flow, tracking, provider credentials or browser-side judging. The former OpenAI Sites checkout is historical and is no longer the publishing source.
