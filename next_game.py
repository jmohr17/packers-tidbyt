import json
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests


ESPN_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/football/nfl/"
    "teams/gb/schedule?season=2026&seasontype=1"
)

ODDS_API_URL = "https://api.odds-api.io/v3"
ODDS_CACHE_FILE = "/tmp/packers_odds.json"
ODDS_CACHE_SECONDS = 600
LOCAL_TIMEZONE = ZoneInfo("America/Chicago")


def find_odds_event(opponent_name):
    url = f"{ODDS_API_URL}/events/search"

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


def get_odds(event_id, packers_home):
    url = f"{ODDS_API_URL}/odds"

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
            hdp = market["odds"][0]["hdp"]
            spread = hdp if packers_home else -hdp

        elif market["name"] == "Totals" and market["odds"]:
            total = market["odds"][0]["hdp"]

    return {
        "spread": spread,
        "total": total,
    }


def get_cached_odds(opponent_name, packers_home):
    try:
        with open(ODDS_CACHE_FILE) as file:
            cache = json.load(file)

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

    odds = get_odds(
        odds_event["id"],
        packers_home,
    )

    with open(ODDS_CACHE_FILE, "w") as file:
        json.dump(
            {
                "event_id": odds_event["id"],
                "timestamp": time.time(),
                "odds": odds,
            },
            file,
        )

    return {
        "event_id": odds_event["id"],
        "odds": odds,
    }


def get_next_game():
    response = requests.get(ESPN_URL, timeout=10)
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

        packers_home = packers["homeAway"] == "home"

        odds_data = get_cached_odds(
            opponent["team"]["displayName"],
            packers_home,
        )

        game_time = datetime.fromisoformat(
            event["date"].replace("Z", "+00:00")
        ).astimezone(LOCAL_TIMEZONE)

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
                for team in competitors
                if team["team"]["abbreviation"] == "GB"
            ),
            "opponent_score": next(
                team.get("score")
                for team in competitors
                if team["team"]["abbreviation"] != "GB"
            ),
            "odds_event_id": (
                odds_data["event_id"] if odds_data else None
            ),
            "spread": (
                odds_data["odds"]["spread"] if odds_data else None
            ),
            "total": (
                odds_data["odds"]["total"] if odds_data else None
            ),
        }

    return None


def main():
    game = get_next_game()

    if not game:
        print("No upcoming Packers games.")
        return

    location = "vs" if game["home_away"] == "home" else "@"

    print("Next Packers game:")
    print(f'GB {location} {game["opponent"]}')
    print(f'{game["date"]} at {game["time"]}')
    print(f'Status: {game["status"]}')
    print(
        f'Score: GB {game["packers_score"]} - '
        f'{game["opponent"]} {game["opponent_score"]}'
    )
    print(f'Period: {game["period"]}')
    print(f'Clock: {game["clock"]}')
    print(f'Odds event: {game["odds_event_id"]}')
    print(f'Spread: {game["spread"]}')
    print(f'Total: {game["total"]}')


if __name__ == "__main__":
    main()