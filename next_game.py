import json
import time

ODDS_CACHE_FILE = "/tmp/packers_odds.json"
ODDS_CACHE_SECONDS = 600

def get_cached_odds(opponent_name):
    try:
        with open(ODDS_CACHE_FILE) as f:
            cache = json.load(f)

        if time.time() - cache["timestamp"] < ODDS_CACHE_SECONDS:
            return {
                "event_id": cache["event_id"],
                "odds": cache["odds"],
            }

    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        pass

    odds_event = find_odds_event(opponent_name)

    if not odds_event:
        return None

    odds = get_odds(odds_event["id"])

    with open(ODDS_CACHE_FILE, "w") as f:
        json.dump({
            "event_id": odds_event["id"],
            "timestamp": time.time(),
            "odds": odds,
        }, f)

    return {
        "event_id": odds_event["id"],
        "odds": odds,
    }

import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

URL = (
    "https://site.api.espn.com/apis/site/v2/sports/football/nfl/"
    "teams/gb/schedule?season=2026&seasontype=1"
)

def find_odds_event(opponent_name):
    url = "https://api.odds-api.io/v3/events/search"

    params = {
        "apiKey": os.environ["ODDS_API_KEY"],
        "query": f"Green Bay Packers {opponent_name}",
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    events = response.json()

    for event in events:
        if (
            event["away"] == "Green Bay Packers"
            and opponent_name.lower() in event["home"].lower()
        ):
            return event

    return None

def get_odds(event_id):
    url = "https://api.odds-api.io/v3/odds"

    params = {
        "apiKey": os.environ["ODDS_API_KEY"],
        "eventId": event_id,
        "bookmakers": "DraftKings",
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    draftkings = data.get("bookmakers", {}).get("DraftKings", [])

    spread = None
    total = None

    for market in draftkings:
        if market["name"] == "Spread" and market["odds"]:
            spread = market["odds"][0]["hdp"]
            spread = f"-{spread}"

        elif market["name"] == "Totals" and market["odds"]:
            total = market["odds"][0]["hdp"]

    return {
        "spread": spread,
        "total": total,
    }

def get_next_game():
    response = requests.get(URL, timeout=10)
    response.raise_for_status()

    data = response.json()

    for event in data["events"]:
        competition = event["competitions"][0]
        status = competition.get("status", {}).get("type", {})

        if status.get("completed", False):
            continue

        competitors = competition["competitors"]

        packers = next(
            team
            for team in competitors
            if team["team"]["abbreviation"] == "GB"
        )

        opponent = next(
            team
            for team in competitors
            if team["team"]["abbreviation"] != "GB"
        )

        odds_data = get_cached_odds(opponent["team"]["displayName"])

        game_time = datetime.fromisoformat(
            event["date"].replace("Z", "+00:00")
        ).astimezone(ZoneInfo("America/Chicago"))

        return {
            "opponent": opponent["team"]["abbreviation"],
            "opponent_name": opponent["team"]["displayName"],
            "home_away": packers["homeAway"],
            "date": game_time.strftime("%a, %b %-d"),
            "time": game_time.strftime("%-I:%M %p"),
            "status": competition["status"]["type"]["state"],
            "period": competition["status"]["period"],
            "clock": competition["status"]["displayClock"],
            "packers_score": next(
                team.get("score")
                for team in competition["competitors"]
                if team["team"]["abbreviation"] == "GB"
            ),
            "opponent_score": next(
                team.get("score")
                for team in competition["competitors"]
                if team["team"]["abbreviation"] != "GB"
            ),
            "odds_event_id": odds_data["event_id"] if odds_data else None,
            "spread": odds_data["odds"]["spread"] if odds_data else None,
            "total": odds_data["odds"]["total"] if odds_data else None,
        }

    return None

if __name__ == "__main__":
    game = get_next_game()

    if game:
        location = "vs" if game["home_away"] == "home" else "@"

        print("Next Packers game:")
        print(f'GB {location} {game["opponent"]}')
        print(f'{game["date"]} at {game["time"]}')
        print(f'Status: {game["status"]}')
        print(f'Score: GB {game["packers_score"]} - {game["opponent"]} {game["opponent_score"]}')
        print(f'Period: {game["period"]}')
        print(f'Clock: {game["clock"]}')
        print(f'Odds event: {game["odds_event_id"]}')
        print(f'Spread: {game["spread"]}')
        print(f'Total: {game["total"]}')
    else:
        print("No upcoming Packers games.")