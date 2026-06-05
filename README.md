# SportsCal

Subscribable `.ics` calendars for the Yankees and Knicks.

## Feeds

Once GitHub Pages is enabled, the feeds will be at:

- `https://<your-user>.github.io/SportsCal/yankees.ics`
- `https://<your-user>.github.io/SportsCal/knicks.ics`

Subscribe on iPhone/Mac by tapping (or pasting) the `webcal://` form, e.g.:

```
webcal://<your-user>.github.io/SportsCal/yankees.ics
```

## What's in each event

- Title: `⚾️ Blue Jays at Yankees` or `🏀 Knicks at Celtics` (away at home)
- Location: venue + city, e.g. `Yankee Stadium, Bronx, NY`
- Start: official first pitch / tip-off (local time, properly UTC-encoded)
- End: start + 3h 15m (MLB) or 2h 30m (NBA) — rough block, not real game length

## How it stays up to date

GitHub Actions runs `build_calendars.py` daily at 6am ET, regenerates the
`.ics` files into `docs/`, and republishes via GitHub Pages.

## Run locally

```bash
pip install -r requirements.txt
python build_calendars.py
# outputs docs/yankees.ics and docs/knicks.ics
```

## Data sources

- Yankees: MLB StatsAPI (`statsapi.mlb.com`)
- Knicks: ESPN's public site API (`site.api.espn.com`)
