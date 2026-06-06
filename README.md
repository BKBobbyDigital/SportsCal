# SportsCal

Subscribable `.ics` calendars for the Yankees and Knicks.

## Available teams

| Team | League | Subscribe (webcal) | Raw .ics |
| --- | --- | --- | --- |
| ⚾️ Yankees | MLB | `webcal://bkbobbydigital.github.io/SportsCal/yankees.ics` | [yankees.ics](https://bkbobbydigital.github.io/SportsCal/yankees.ics) |
| ⚾️ Phillies | MLB | `webcal://bkbobbydigital.github.io/SportsCal/phillies.ics` | [phillies.ics](https://bkbobbydigital.github.io/SportsCal/phillies.ics) |
| 🏀 Knicks | NBA | `webcal://bkbobbydigital.github.io/SportsCal/knicks.ics` | [knicks.ics](https://bkbobbydigital.github.io/SportsCal/knicks.ics) |

Tap a `webcal://` link on iPhone or Mac to subscribe directly in Calendar.

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
