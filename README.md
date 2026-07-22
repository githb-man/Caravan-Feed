# Caravan Magazine — Unofficial RSS Feed

`caravanmagazine.in` doesn't publish an RSS feed. This scrapes the homepage
on a schedule and publishes a proper RSS feed for free, using only GitHub
(no third-party service, no signup elsewhere).

## Setup (~5 minutes, one time)

1. **Create a new GitHub repo** and upload everything in this folder to it
   (or `git init` here and push). It can be public or private — if private,
   your feed URL will need a personal access token to access, so **public**
   is simpler unless you want it private.

2. **Enable GitHub Pages**:
   - Go to your repo → **Settings → Pages**
   - Under "Build and deployment" → Source: **Deploy from a branch**
   - Branch: `main`, folder: `/docs` → Save

3. **Run the workflow once manually** so `docs/feed.xml` exists:
   - Go to the **Actions** tab → "Update Caravan RSS feed" → **Run workflow**
   - Wait ~30 seconds for it to finish (green check)

4. **Get your feed URL**. It'll be:
   ```
   https://<your-github-username>.github.io/<repo-name>/feed.xml
   ```
   GitHub shows the exact URL under Settings → Pages once it's live.

5. Paste that URL into your RSS reader. Done — it'll refresh automatically
   every 2 hours forever, for free, via GitHub Actions' free tier (well
   within the free minutes for a job this small).

## If it stops finding articles

Caravan's site markup could change at some point, in which case the scraper
will fail loudly (the Action will show a red X) instead of silently
producing an empty feed. If that happens, send me the current HTML of
https://caravanmagazine.in/ (or just tell me it broke) and I'll update the
selector logic in `scraper/scrape.py`.

## How dates work

The site doesn't show publish dates on the homepage, so `pubDate` in the
feed is "the first time this scraper saw the article" — accurate to within
the 2-hour polling window. Articles are kept in the feed for 30 days after
first being seen, then aged out automatically.

## Adjusting frequency

Edit the `cron` line in `.github/workflows/update-feed.yml`. E.g. every
hour: `"0 * * * *"`. Don't go much more frequent than that — no need to
hammer their homepage.
