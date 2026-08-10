import time
from datetime import datetime, timezone
from nfl import get_packers_schedule, calculate_record, get_next_game


WIDTH = 32


def line(char="─"):
    return char * WIDTH


def center(text):
    return text.center(WIDTH)


def show_next_game_page():
    games = get_packers_schedule()

    wins, losses, ties = calculate_record(games)
    next_game = get_next_game(games)

    print()
    print("┌" + line() + "┐")
    print("│" + center("PACKERS") + "│")
    print("│" + center(f"{wins}-{losses}") + "│")
    print("├" + line() + "┤")
    print("│" + center("NEXT GAME") + "│")

    if next_game:
        location = (
            "vs"
            if next_game["home_away"] == "home"
            else "@"
        )

        opponent = (
            f'{location} '
            f'{next_game["opponent_abbreviation"]}'
        )

        date = next_game["local_date"]

        print("│" + center(opponent) + "│")
        print("│" + center(date) + "│")
    else:
        print("│" + center("NO UPCOMING GAME") + "│")

    print("└" + line() + "┘")
    print()

def show_schedule_page():
    games = get_packers_schedule()

    print()
    print("┌" + line() + "┐")
    print("│" + center("PACKERS SCHEDULE") + "│")
    print("├" + line() + "┤")

    for game in games:
        location = (
            "vs"
            if game["home_away"] == "home"
            else "@"
        )

        opponent = game["opponent_abbreviation"]
        week = game["week"]
        date = game["local_date"]

        print(
            "│" +
            f"{week:<10}{location} {opponent}".ljust(WIDTH) +
            "│"
        )

        print(
            "│" +
            f"{date}".center(WIDTH) +
            "│"
        )

        print("│" + " " * WIDTH + "│")

    print("└" + line() + "┘")
    print()

def show_record_page():
    games = get_packers_schedule()

    wins, losses, ties = calculate_record(games)
    games_played = wins + losses + ties

    print()
    print("┌" + line() + "┐")
    print("│" + center("PACKERS RECORD") + "│")
    print("├" + line() + "┤")
    print("│" + " " * WIDTH + "│")
    print("│" + center(f"{wins} - {losses}") + "│")
    print("│" + " " * WIDTH + "│")
    print("│" + center(f"{games_played} GAMES PLAYED") + "│")
    print("│" + " " * WIDTH + "│")
    print("└" + line() + "┘")
    print()

def show_countdown_page():
    games = get_packers_schedule()
    next_game = get_next_game(games)

    print()
    print("┌" + line() + "┐")
    print("│" + center("PACKERS COUNTDOWN") + "│")
    print("├" + line() + "┤")

    if next_game:
        game_time = datetime.fromisoformat(
            next_game["date"].replace("Z", "+00:00")
        )

        now = datetime.now(timezone.utc)

        time_remaining = game_time - now
        total_seconds = int(time_remaining.total_seconds())

        if total_seconds > 0:
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            minutes = (total_seconds % 3600) // 60

            location = (
                "vs"
                if next_game["home_away"] == "home"
                else "@"
            )

            opponent = (
                f'{location} '
                f'{next_game["opponent_abbreviation"]}'
            )

            print("│" + " " * WIDTH + "│")
            print("│" + center ("GB "+ opponent) + "│")
            print("│" + " " * WIDTH + "│")
            print("│" + center(f"{days} DAYS") + "│")
            print("│" + center(
                f"{hours} HR {minutes} MIN"
            ) + "│")
            print("│" + " " * WIDTH + "│")

        else:
            print("│" + center("GAME DAY!") + "│")

    else:
        print("│" + " " * WIDTH + "│")
        print("│" + center("NO UPCOMING GAME") + "│")
        print("│" + " " * WIDTH + "│")

    print("└" + line() + "┘")
    print()

def run_app():
    pages = [
        show_next_game_page,
        show_countdown_page,
        show_record_page,
        show_schedule_page,
    ]

    while True:
        for page in pages:
            page()
            time.sleep(5)

if __name__ == "__main__":
    run_app()