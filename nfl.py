import requests
from datetime import datetime
from zoneinfo import ZoneInfo


URL = (
    "https://site.api.espn.com/apis/site/v2/sports/football/nfl/"
    "teams/gb/schedule?season=2026&seasontype=2"
)


def get_packers_schedule():
    response = requests.get(URL)
    response.raise_for_status()

    data = response.json()
    games = []

    for event in data["events"]:
        competition = event["competitions"][0]
        competitors = competition["competitors"]

        packers = next(
            team for team in competitors
            if team["team"]["abbreviation"] == "GB"
        )

        opponent = next(
            team for team in competitors
            if team["team"]["abbreviation"] != "GB"
        )

        status = competition.get("status", {}).get("type", {})

        game = {
            "id": event["id"],
            "date": event["date"],
            "local_date": format_game_time(event["date"]),
            "week": event["week"]["text"],
            "home_away": packers["homeAway"],
            "opponent": opponent["team"]["displayName"],
            "opponent_abbreviation": opponent["team"]["abbreviation"],
            "status": status.get("description", "Unknown"),
            "completed": status.get("completed", False),
        }

        if "score" in packers and "score" in opponent:
            game["packers_score"] = int(packers["score"])
            game["opponent_score"] = int(opponent["score"])

            if game["completed"]:
                if game["packers_score"] > game["opponent_score"]:
                    game["result"] = "WIN"
                elif game["packers_score"] < game["opponent_score"]:
                    game["result"] = "LOSS"
                else:
                    game["result"] = "TIE"

        games.append(game)

    return games

def format_game_time(date_string):
    utc_time = datetime.fromisoformat(date_string.replace("Z", "+00:00"))

    local_time = utc_time.astimezone(
        ZoneInfo("America/Chicago")
    )

    return local_time.strftime("%a, %b %-d at %-I:%M %p")

def calculate_record(games):
    wins = 0
    losses = 0
    ties = 0

    for game in games:
        if not game["completed"]:
            continue

        if game["result"] == "WIN":
            wins += 1
        elif game["result"] == "LOSS":
            losses += 1
        elif game["result"] == "TIE":
            ties += 1
    return wins, losses, ties

def get_next_game(games):
    upcoming_games = [
        game for game in games
        if not game["completed"]
    ]

    if not upcoming_games:
        return None

    upcoming_games.sort(key=lambda game: game["date"])

    return upcoming_games[0]

if __name__ == "__main__":
    games = get_packers_schedule()

    wins, losses, ties = calculate_record(games)

    next_game = get_next_game(games)

    if next_game:
        location = "vs" if next_game["home_away"] == "home" else "@"

        print("\nNext Packers game:")
        print(
            f'{location} {next_game["opponent_abbreviation"]} '
            f'- {format_game_time(next_game["date"])}'
    )

    print(f"Packers Record: {wins}-{losses}-{ties}")
    print(f"Games played: {wins + losses + ties}\n")

    print(f"Found {len(games)} Packers games\n")

    for game in games:
        location = "vs" if game["home_away"] == "home" else "@"

        if game["completed"]:
            score = (
                f'{game["packers_score"]}-'
                f'{game["opponent_score"]} '
                f'{game["result"]}'
            )
        else:
            score = game["status"]

        print(
            f'{game["week"]:18} '
            f'{location} {game["opponent_abbreviation"]:3} '
            f'{game["local_date"]} '
            f'({score})'
        )