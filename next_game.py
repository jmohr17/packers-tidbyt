import json
import os
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests


ESPN_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/football/nfl/"
    "teams/gb/schedule?season=2026&seasontype=1"
)

ODDS_API_URL = "https://api.odds-api.io/v3"
ODDS_CACHE_FILE = os.path.expanduser(
    "~/.cache/packers-tidbyt/odds.json"
)
ODDS_CACHE_SECONDS = 600
POST_GAME_HOLD_HOURS = 48
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
            home_spread = market["odds"][0]["hdp"]
            spread = home_spread if packers_home else -home_spread

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

        cache_age = time.time() - cache["timestamp"]

        if (
            cache["opponent_name"] == opponent_name
            and cache_age < ODDS_CACHE_SECONDS
        ):
            return {
                "event_id": cache["event_id"],
                "odds": cache["odds"],
            }

    except (
        FileNotFoundError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
    ):
        pass

    odds_event = find_odds_event(opponent_name)

    if not odds_event:
        return None

    odds = get_odds(
        odds_event["id"],
        packers_home,
    )

    cache_directory = os.path.dirname(ODDS_CACHE_FILE)
    os.makedirs(cache_directory, exist_ok=True)

    with open(ODDS_CACHE_FILE, "w") as file:
        json.dump(
            {
                "event_id": odds_event["id"],
                "opponent_name": opponent_name,
                "timestamp": time.time(),
                "odds": odds,
            },
            file,
        )

    return {
        "event_id": odds_event["id"],
        "odds": odds,
    }


def build_game(event, get_odds_data=True):
    competition = event["competitions"][0]
    status = competition.get("status", {}).get("type", {})

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

    game_time = datetime.fromisoformat(
        event["date"].replace("Z", "+00:00")
    ).astimezone(LOCAL_TIMEZONE)

    odds_data = None

    # Don't make an Odds API call for a completed game.
    if get_odds_data and not status.get("completed", False):
        odds_data = get_cached_odds(
            opponent["team"]["displayName"],
            packers_home,
        )

    return {
        "event_time": game_time,
        "opponent": opponent["team"]["abbreviation"],
        "opponent_name": opponent["team"]["displayName"],
        "home_away": packers["homeAway"],
        "date": game_time.strftime("%a, %b %-d"),
        "time": game_time.strftime("%-I:%M %p"),
        "status": competition["status"]["type"]["state"],
        "period": competition["status"]["period"],
        "clock": competition["status"]["displayClock"],
        "packers_score": next(
            team.get("score", {}).get("displayValue")
            if isinstance(team.get("score"), dict)
            else team.get("score")
            for team in competitors
            if team["team"]["abbreviation"] == "GB"
        ),
        "opponent_score": next(
            team.get("score", {}).get("displayValue")
            if isinstance(team.get("score"), dict)
            else team.get("score")
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


def get_next_game():
    response = requests.get(ESPN_URL, timeout=10)
    response.raise_for_status()

    data = response.json()

    now = datetime.now(LOCAL_TIMEZONE)
    post_game_cutoff = now - timedelta(
        hours=POST_GAME_HOLD_HOURS
    )

    recent_completed_game = None
    recent_completed_time = None

    upcoming_game = None
    upcoming_game_time = None

    for event in data["events"]:
        competition = event["competitions"][0]
        status = competition.get("status", {}).get("type", {})

        game_time = datetime.fromisoformat(
            event["date"].replace("Z", "+00:00")
        ).astimezone(LOCAL_TIMEZONE)

        if status.get("completed", False):
            # Keep the most recently completed game visible
            # for 48 hours after its scheduled start time.
            if (
                post_game_cutoff <= game_time <= now
            ):
                if (
                    recent_completed_time is None
                    or game_time > recent_completed_time
                ):
                    recent_completed_game = event
                    recent_completed_time = game_time

        else:
            if game_time >= now:
                if (
                    upcoming_game_time is None
                    or game_time < upcoming_game_time
                ):
                    upcoming_game = event
                    upcoming_game_time = game_time

    # A recently completed game takes priority over the next
    # upcoming game.
    if recent_completed_game is not None:
        return build_game(
            recent_completed_game,
            get_odds_data=False,
        )

    if upcoming_game is not None:
        return build_game(
            upcoming_game,
            get_odds_data=True,
        )

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