import requests
from datetime import datetime
from zoneinfo import ZoneInfo

URL = (
    "https://site.api.espn.com/apis/site/v2/sports/football/nfl/"
    "teams/gb/schedule?season=2026&seasontype=1"
)


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

        game_time = datetime.fromisoformat(
            event["date"].replace("Z", "+00:00")
        ).astimezone(ZoneInfo("America/Chicago"))

        return {
            "opponent": opponent["team"]["abbreviation"],
            "opponent_name": opponent["team"]["displayName"],
            "home_away": packers["homeAway"],
            "date": game_time.strftime("%a, %b %-d"),
            "time": game_time.strftime("%-I:%M %p"),
        }

    return None


if __name__ == "__main__":
    game = get_next_game()

    if game:
        location = "vs" if game["home_away"] == "home" else "@"

        print("Next Packers game:")
        print(f'GB {location} {game["opponent"]}')
        print(f'{game["date"]} at {game["time"]}')
    else:
        print("No upcoming Packers games.")