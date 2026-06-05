"""
SportsCal — generates subscribable .ics calendars for the Yankees and Knicks.

Output: docs/yankees.ics, docs/knicks.ics
Hosted via GitHub Pages; subscribe with webcal:// in Apple/Google Calendar.

No external dependencies beyond the Python stdlib + `requests`.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import os
from pathlib import Path

import requests

OUT_DIR = Path(__file__).parent / "docs"
OUT_DIR.mkdir(exist_ok=True)

# Rolling window: ~14 months back (covers full current MLB season and the
# Oct-start of the current/most-recent NBA season) through next 6 months.
TODAY = dt.date.today()
WINDOW_START = TODAY - dt.timedelta(days=425)
WINDOW_END = TODAY + dt.timedelta(days=183)

BASEBALL = "⚾️"   # ⚾️
BASKETBALL = "\U0001F3C0"   # 🏀

# Rough game-length estimates so calendar blocks look right
MLB_DURATION = dt.timedelta(hours=3, minutes=15)
NBA_DURATION = dt.timedelta(hours=2, minutes=30)


# ----------------------------- ICS helpers -----------------------------

def ics_escape(s: str) -> str:
    if s is None:
        return ""
    return (
        s.replace("\\", "\\\\")
         .replace(";", "\\;")
         .replace(",", "\\,")
         .replace("\n", "\\n")
    )


def fmt_utc(d: dt.datetime) -> str:
    return d.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def build_ics(cal_name: str, events: list[dict]) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//SportsCal//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{ics_escape(cal_name)}",
        f"NAME:{ics_escape(cal_name)}",
        "REFRESH-INTERVAL;VALUE=DURATION:PT6H",
        "X-PUBLISHED-TTL:PT6H",
    ]
    now_stamp = fmt_utc(dt.datetime.now(dt.timezone.utc))
    for ev in events:
        lines += [
            "BEGIN:VEVENT",
            f"UID:{ev['uid']}",
            f"DTSTAMP:{now_stamp}",
            f"DTSTART:{fmt_utc(ev['start'])}",
            f"DTEND:{fmt_utc(ev['end'])}",
            f"SUMMARY:{ics_escape(ev['summary'])}",
            f"LOCATION:{ics_escape(ev['location'])}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    # ICS spec wants CRLF line endings
    return "\r\n".join(lines) + "\r\n"


def write_calendar(filename: str, cal_name: str, events: list[dict]) -> None:
    path = OUT_DIR / filename
    path.write_text(build_ics(cal_name, events))
    print(f"  wrote {path} ({len(events)} events)")


# ----------------------------- Yankees (MLB StatsAPI) -----------------------------

YANKEES_TEAM_ID = 147

def fetch_yankees() -> list[dict]:
    url = "https://statsapi.mlb.com/api/v1/schedule"
    params = {
        "teamId": YANKEES_TEAM_ID,
        "sportId": 1,
        "startDate": WINDOW_START.isoformat(),
        "endDate": WINDOW_END.isoformat(),
        "hydrate": "venue(location)",
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    events = []
    for day in data.get("dates", []):
        for game in day.get("games", []):
            game_pk = game["gamePk"]
            status = game.get("status", {}).get("abstractGameState", "")
            # Skip cancelled; postponed games stay (they'll be rescheduled w/ new gamePk)
            if status == "Cancelled":
                continue

            start_iso = game["gameDate"]  # already in UTC ISO8601 (...Z)
            start = dt.datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
            end = start + MLB_DURATION

            home = game["teams"]["home"]["team"]["name"]
            away = game["teams"]["away"]["team"]["name"]
            # Title format: "⚾️ Away at Home"
            summary = f"{BASEBALL} {away} at {home}"

            venue = game.get("venue", {})
            venue_name = venue.get("name", "")
            loc_parts = [venue_name]
            # /schedule with hydrate=venue returns city/state in venue.location
            vloc = venue.get("location", {}) if isinstance(venue.get("location"), dict) else {}
            city = vloc.get("city")
            state = vloc.get("stateAbbrev") or vloc.get("state")
            if city and state:
                loc_parts.append(f"{city}, {state}")
            elif city:
                loc_parts.append(city)
            location = ", ".join(p for p in loc_parts if p)

            events.append({
                "uid": f"mlb-{game_pk}@sportscal",
                "start": start,
                "end": end,
                "summary": summary,
                "location": location,
            })
    return events


# ----------------------------- Knicks (ESPN) -----------------------------

KNICKS_TEAM_ID = 18  # ESPN's NBA team id for the Knicks

def fetch_knicks() -> list[dict]:
    # ESPN's "season" param is the year the NBA season ENDS.
    # Pull prior + current to cover the past-season backfill, and next if we're
    # already in the offseason where the upcoming schedule has been published.
    seasons = [TODAY.year - 1, TODAY.year]
    if TODAY.month >= 7:
        seasons.append(TODAY.year + 1)

    seen = set()
    events = []
    # ESPN seasontype: 1=preseason, 2=regular season, 3=postseason. We want all three.
    for season in seasons:
        for seasontype in (1, 2, 3):
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{KNICKS_TEAM_ID}/schedule"
            try:
                r = requests.get(url, params={"season": season, "seasontype": seasontype}, timeout=30)
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                print(f"  warn: knicks season {season} type {seasontype} fetch failed: {e}")
                continue

            for game in data.get("events", []):
                gid = game.get("id")
                if not gid or gid in seen:
                    continue
                seen.add(gid)

                start_iso = game.get("date")
                if not start_iso:
                    continue
                start = dt.datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
                if not (WINDOW_START <= start.date() <= WINDOW_END):
                    continue

                comp = (game.get("competitions") or [{}])[0]
                competitors = comp.get("competitors", [])
                home_team = away_team = None
                for c in competitors:
                    team_name = c.get("team", {}).get("displayName", "")
                    if c.get("homeAway") == "home":
                        home_team = team_name
                    elif c.get("homeAway") == "away":
                        away_team = team_name
                if not home_team or not away_team:
                    continue

                summary = f"{BASKETBALL} {away_team} at {home_team}"

                venue = comp.get("venue", {}) or {}
                venue_name = venue.get("fullName", "")
                vaddr = venue.get("address", {}) or {}
                city = vaddr.get("city")
                state = vaddr.get("state")
                loc_parts = [venue_name]
                if city and state:
                    loc_parts.append(f"{city}, {state}")
                elif city:
                    loc_parts.append(city)
                location = ", ".join(p for p in loc_parts if p)

                end = start + NBA_DURATION
                events.append({
                    "uid": f"nba-{gid}@sportscal",
                    "start": start,
                    "end": end,
                    "summary": summary,
                    "location": location,
                })
    return events


# ----------------------------- main -----------------------------

def main() -> None:
    print("Building Yankees calendar...")
    yankees = fetch_yankees()
    write_calendar("yankees.ics", "Yankees", yankees)

    print("Building Knicks calendar...")
    knicks = fetch_knicks()
    write_calendar("knicks.ics", "Knicks", knicks)

    # Simple landing page so the Pages root isn't a 404
    index = OUT_DIR / "index.html"
    index.write_text(
        "<!doctype html><meta charset=utf-8><title>SportsCal</title>"
        "<h1>SportsCal</h1>"
        "<p>Subscribe in your calendar app:</p>"
        "<ul>"
        '<li>Yankees: <code>yankees.ics</code></li>'
        '<li>Knicks: <code>knicks.ics</code></li>'
        "</ul>"
    )

if __name__ == "__main__":
    main()
